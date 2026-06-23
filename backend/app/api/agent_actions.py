"""
api/agent_actions.py — Human-in-the-loop agent action endpoints.

Lets a dashboard operator act on a conversation that the bot started:
  - PATCH /api/sessions/{id}/status   → resolve / escalate / reopen / take over
  - POST  /api/sessions/{id}/reply    → send a manual WhatsApp reply as the tenant

These turn the dashboard from a passive monitor into a real agent tool and
make the NEEDS_HUMAN status a genuine safety valve (operators can clear the queue).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.db.models import (
    SessionUpdateRequest,
    SessionStatusUpdateResponse,
    AgentReplyRequest,
    AgentReplyResponse,
    Message, MessageDirection, MessageType, MessageStatus,
    SessionStatus,
)
from app.db.repositories import session_repo, message_repo, tenant_repo
from app.services.whatsapp import WhatsAppService
from app.api.sse import broadcast_event

logger = logging.getLogger(__name__)
router = APIRouter()


@router.patch("/sessions/{session_id}/status", response_model=SessionStatusUpdateResponse)
async def update_session_status(
    session_id: str,
    request: SessionUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Manually transition a session's status.

    Used by: Resolve, Escalate, Reopen, and Take-over buttons in the dashboard.
    """
    session = await session_repo.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Take-over escalates to AGENT_HANDOFF so the bot stops auto-replying
    await session_repo.update_session_status(db, session_id, request.status)

    # Append a system audit message so the thread records the action
    system_msg = Message(
        session_id=session_id,
        tenant_id=session.tenant_id,
        direction=MessageDirection.OUTBOUND,
        sender=request.agent_id or "dashboard_operator",
        message_type=MessageType.SYSTEM,
        text_content=f"[Status changed to {request.status.value} by {request.agent_id or 'operator'}]",
        agent_state_snapshot={"action": "status_change", "new_status": request.status.value},
    )
    await message_repo.save_message(db, system_msg)
    await session_repo.increment_message_count(db, session_id)

    # Notify the dashboard in real time
    await broadcast_event(
        tenant_id=session.tenant_id,
        event_type="session_updated",
        data={
            "session_id": session_id,
            "status": request.status.value,
            "customer_phone": session.customer_phone,
        },
    )

    logger.info(f"🔧 Session {session_id} status → {request.status.value} by {request.agent_id}")
    return SessionStatusUpdateResponse(session_id=session_id, status=request.status)


@router.post("/sessions/{session_id}/reply", response_model=AgentReplyResponse)
async def send_agent_reply(
    session_id: str,
    request: AgentReplyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Send a manual text reply from the dashboard straight to the customer's WhatsApp.

    Used when an operator takes over a NEEDS_HUMAN session. The reply goes out via
    the tenant's WhatsApp number, is logged as an outbound message, and the session
    flips to AGENT_HANDOFF so the bot does not auto-reply on the next inbound.
    """
    session = await session_repo.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    tenant = await tenant_repo.get_tenant_by_id(db, session.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    wa_message_id = None
    try:
        wa = WhatsAppService()
        wa_resp = await wa.send_text(
            phone_number_id=tenant.phone_number_id,
            to=session.customer_phone,
            text=request.text,
            token=tenant.whatsapp_token,
        )
        # Twilio returns {"sid": "SM...", "status": "queued"}
        wa_message_id = wa_resp.get("sid")
    except Exception as e:
        logger.error(f"Manual reply failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to send WhatsApp message: {e}")

    # Persist the outbound message (delivery_status=SENT; updated on webhook status callback)
    outbound = Message(
        session_id=session_id,
        tenant_id=session.tenant_id,
        direction=MessageDirection.OUTBOUND,
        sender=request.agent_id or "dashboard_operator",
        message_type=MessageType.TEXT,
        text_content=request.text,
        wa_message_id=wa_message_id,
        delivery_status=MessageStatus.SENT.value,
        agent_state_snapshot={"source": "manual_agent_reply", "agent_id": request.agent_id},
    )
    saved = await message_repo.save_message(db, outbound)
    await session_repo.increment_message_count(db, session_id)

    # Mark as AGENT_HANDOFF so the bot yields control
    await session_repo.update_session_status(db, session_id, SessionStatus.AGENT_HANDOFF)

    # Live-update the dashboard thread
    await broadcast_event(
        tenant_id=session.tenant_id,
        event_type="new_message",
        data={
            "session_id": session_id,
            "message_id": saved.id,
            "customer_phone": session.customer_phone,
            "message_type": "text",
            "text_content": request.text,
            "direction": "outbound",
        },
    )
    await broadcast_event(
        tenant_id=session.tenant_id,
        event_type="session_updated",
        data={"session_id": session_id, "status": SessionStatus.AGENT_HANDOFF.value},
    )

    logger.info(f"📤 Manual agent reply sent to {session.customer_phone} (session {session_id})")
    return AgentReplyResponse(
        session_id=session_id,
        message_id=saved.id,
        wa_message_id=wa_message_id,
        status=SessionStatus.AGENT_HANDOFF,
    )
