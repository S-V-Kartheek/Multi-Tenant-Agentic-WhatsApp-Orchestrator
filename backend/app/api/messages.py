"""
api/messages.py — REST endpoints for message history retrieval.

Powers the chat thread view in the dashboard, showing all inbound/outbound
messages for a selected session including media indicators and delivery status.
Supports cursor-based pagination for infinite scroll-up through history.
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.db.models import MessageResponse
from app.db.repositories import message_repo

router = APIRouter()


def _to_response(m) -> MessageResponse:
    return MessageResponse(
        id=m.id,
        session_id=m.session_id,
        direction=m.direction,
        sender=m.sender,
        message_type=m.message_type,
        text_content=m.text_content,
        media_url=m.media_url,
        media_mime_type=m.media_mime_type,
        media_filename=m.media_filename,
        delivery_status=m.delivery_status,
        agent_state_snapshot=m.agent_state_snapshot or {},
        timestamp=m.timestamp,
    )


@router.get("/messages/{session_id}", response_model=list[MessageResponse])
async def get_messages(
    session_id: str,
    limit: int = 50,
    before_id: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Retrieve messages for a chat session, sorted oldest-first.

    Query params:
      - limit: max messages per page
      - before_id: ObjectId of the oldest currently-loaded message (for infinite scroll-up)
    """
    messages = await message_repo.get_messages_by_session(db, session_id, limit, before_id)
    return [_to_response(m) for m in messages]
