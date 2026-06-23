"""
api/agent_runs.py — LangGraph run trace endpoints.

Exposes per-run and per-session agent execution traces so the dashboard's
Run Trace Viewer can visualize how state flows through the 4-node graph.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.db.models import AgentRunResponse
from app.db.repositories import agent_run_repo

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_response(run) -> AgentRunResponse:
    return AgentRunResponse(
        id=run.id,
        tenant_id=run.tenant_id,
        session_id=run.session_id,
        customer_phone=run.customer_phone,
        inbound_text=run.inbound_text,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_ms=run.duration_ms,
        steps=run.steps,
        tool_chosen=run.tool_chosen,
        response_type=run.response_type,
        sentiment_score=run.sentiment_score,
        escalated=run.escalated,
        error=run.error,
    )


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run(run_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Fetch a single agent run trace by ID — for the Run Trace Viewer."""
    run = await agent_run_repo.get_run_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _to_response(run)


@router.get("/runs/sessions/{session_id}", response_model=list[AgentRunResponse])
async def get_runs_for_session(
    session_id: str,
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """All run traces for a conversation — used to browse past decisions per chat."""
    runs = await agent_run_repo.get_runs_by_session(db, session_id, limit)
    return [_to_response(r) for r in runs]


@router.get("/runs/tenants/{tenant_id}", response_model=list[AgentRunResponse])
async def get_runs_for_tenant(
    tenant_id: str,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Recent run traces for a tenant — for the analytics recent-runs feed."""
    runs = await agent_run_repo.get_runs_by_tenant(db, tenant_id, limit)
    return [_to_response(r) for r in runs]
