"""
agent/trace.py — Helpers for recording per-node steps into the agent_run trace.

Each node wraps its work in `trace_step()` which stamps a start/finish timestamp,
computes duration, and appends a snapshot of the relevant state slice. This is
what powers the dashboard's Run Trace Viewer — a direct visualization of how
state flows through the LangGraph graph.
"""
import functools
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories import agent_run_repo

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _sanitize_snapshot(state: dict, keys: list[str]) -> dict:
    """Pull a safe subset of state into the trace snapshot."""
    snapshot = {}
    for k in keys:
        if k in state and state[k] is not None:
            val = state[k]
            # Truncate long text to keep the document lean
            if isinstance(val, str) and len(val) > 500:
                val = val[:500] + "…"
            snapshot[k] = val
    return snapshot


async def record_step(
    db: AsyncIOMotorDatabase,
    state: dict,
    node: str,
    status: str,
    snapshot_keys: list[str] | None = None,
    started_at: datetime | None = None,
) -> None:
    """Append a completed step to the run trace (best-effort — never fails the pipeline)."""
    run_id = state.get("run_id")
    if not run_id:
        return
    try:
        await agent_run_repo.add_step(
            db=db,
            run_id=run_id,
            node=node,
            status=status,
            snapshot=_sanitize_snapshot(state, snapshot_keys or []),
            started_at=started_at,
            finished_at=_utcnow(),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"trace.record_step failed for {node}: {e}")


def traced_node(node_name: str, snapshot_keys: list[str] | None = None):
    """
    Decorator for agent nodes. Records a start step before the node runs and a
    completed/failed step after, capturing the per-node duration used by the
    Run Trace Viewer. The wrapped node must be an async function (state, db).
    """
    def decorator(fn: Callable[..., Awaitable[dict]]):
        @functools.wraps(fn)
        async def wrapper(state: dict, db: AsyncIOMotorDatabase, *args, **kwargs):
            started = _utcnow()
            run_id = state.get("run_id")
            # Record the "running" phase so the trace shows the node firing live
            if run_id:
                try:
                    await agent_run_repo.add_step(
                        db=db, run_id=run_id, node=node_name, status="running",
                        snapshot={}, started_at=started, finished_at=None,
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"trace start failed for {node_name}: {e}")

            try:
                update = await fn(state, db, *args, **kwargs)
                # Merge update into a copy of state so the snapshot reflects post-node values
                merged = {**state, **(update or {})}
                await record_step(db, merged, node_name, "completed", snapshot_keys, started)
                return update
            except Exception as e:
                merged = {**state, "error_message": str(e)}
                await record_step(db, merged, node_name, "failed", snapshot_keys, started)
                raise
        return wrapper
    return decorator
