"""
api/metrics.py — Analytics aggregation endpoint for the dashboard.

Returns a single bundle of KPIs for a tenant: session counts, resolution rate,
avg resolution time, avg sentiment, message volume trends, status distribution,
message-type distribution, and recent agent runs. The frontend renders this as
KPI cards + charts on the Analytics page.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.db.models import TenantMetrics, AgentRunSummary
from app.db.repositories import session_repo, message_repo, agent_run_repo, campaign_repo

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics/{tenant_id}", response_model=TenantMetrics)
async def get_tenant_metrics(
    tenant_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Aggregate all KPIs for a tenant's analytics dashboard.

    Computed in a single endpoint to minimize round-trips from the frontend.
    """
    # Status counts
    status_counts = await session_repo.count_sessions_by_status(db, tenant_id)
    total_sessions = sum(status_counts.values())
    resolved = status_counts.get("RESOLVED", 0)
    needs_human = status_counts.get("NEEDS_HUMAN", 0)

    # An "active" session is anything not yet RESOLVED
    active_sessions = total_sessions - resolved

    resolution_rate = (resolved / total_sessions) if total_sessions > 0 else 0.0

    # Message stats
    msg_stats = await message_repo.get_tenant_message_stats(db, tenant_id)

    # Resolution time + sentiment averages
    avg_resolution = await session_repo.get_avg_resolution_time(db, tenant_id)
    avg_sentiment = await session_repo.get_avg_sentiment(db, tenant_id)

    # Broadcasts sent
    broadcasts_sent = await campaign_repo.count_campaigns_by_tenant(db, tenant_id)

    # Recent agent runs (tool/sentiment feed) — typed as AgentRunSummary
    recent_runs: list[AgentRunSummary] = []
    runs = await agent_run_repo.get_runs_by_tenant(db, tenant_id, limit=8)
    for r in runs:
        recent_runs.append(AgentRunSummary(
            id=r.id,
            session_id=r.session_id,
            customer_phone=r.customer_phone,
            status=r.status.value,
            tool_chosen=r.tool_chosen,
            response_type=r.response_type,
            sentiment_score=r.sentiment_score,
            escalated=r.escalated,
            duration_ms=r.duration_ms,
            started_at=r.started_at.isoformat(),
        ))

    return TenantMetrics(
        tenant_id=tenant_id,
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        resolved_sessions=resolved,
        needs_human_sessions=needs_human,
        resolution_rate=round(resolution_rate, 3),
        total_messages=msg_stats["total"],
        inbound_messages=msg_stats["inbound"],
        outbound_messages=msg_stats["outbound"],
        broadcasts_sent=broadcasts_sent,
        avg_resolution_time_sec=avg_resolution,
        avg_sentiment=avg_sentiment,
        status_distribution=status_counts,
        message_type_distribution=msg_stats["type_distribution"],
        hourly_volume=msg_stats["hourly_volume"],
        daily_volume=msg_stats["daily_volume"],
        recent_runs=recent_runs,
    )
