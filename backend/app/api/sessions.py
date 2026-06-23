"""
api/sessions.py — REST endpoints for chat session management.

Powers the Live Chat Monitor on the dashboard — lists active conversations
with optional search + status filter, and supports per-session inspection.
"""
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.db.models import ChatSessionResponse
from app.db.repositories import session_repo, message_repo

router = APIRouter()


def _to_response(s) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=s.id,
        tenant_id=s.tenant_id,
        customer_phone=s.customer_phone,
        status=s.status,
        message_count=s.message_count,
        last_activity=s.last_activity,
        created_at=s.created_at,
        sentiment_score=getattr(s, "sentiment_score", None),
        last_run_id=getattr(s, "last_run_id", None),
    )


@router.get("/sessions/{tenant_id}", response_model=list[ChatSessionResponse])
async def get_sessions_by_tenant(
    tenant_id: str,
    limit: int = 50,
    status: str = "ALL",
    search: str = "",
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Fetch active chat sessions for a tenant with optional filters.

    Query params:
      - limit: max results
      - status: filter by status (ALL | WAITING_FOR_BOT | AGENT_RESPONDING | RESOLVED | NEEDS_HUMAN | AGENT_HANDOFF)
      - search: substring match on customer_phone
    """
    sessions = await session_repo.get_sessions_by_tenant(
        db, tenant_id, limit=limit, status=status, search=search or None
    )
    return [_to_response(s) for s in sessions]


@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Fetch a single session by ID — used when opening a chat thread."""
    session = await session_repo.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_response(session)


@router.get("/sessions/{session_id}/preview")
async def get_session_preview(session_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Return a last-message snippet for the chat list preview line."""
    session = await session_repo.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    snippet = await message_repo.get_last_message_preview(db, session_id)
    return {"session_id": session_id, "preview": snippet}
