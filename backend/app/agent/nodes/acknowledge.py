"""
agent/nodes/acknowledge.py — LangGraph Node 1: Acknowledge.

This is the FIRST node to execute when a customer message arrives.
It fires off WhatsApp read receipts and typing indicators INSTANTLY
before any LLM processing begins — this is the key UX optimization
that shows "double blue ticks" and "typing..." to reduce user drop-off.

Side effects:
  - Marks message as read on WhatsApp
  - Sends typing indicator
  - Saves inbound message to MongoDB audit log
  - Updates session status to AGENT_RESPONDING
  - Emits SSE event to dashboard
  - Records a trace step for the Run Trace Viewer
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agent.state import AgentState
from app.agent.trace import traced_node
from app.db.models import Message, MessageDirection, MessageType, SessionStatus
from app.db.repositories import session_repo, message_repo
from app.services.whatsapp import WhatsAppService
from app.api.sse import broadcast_event

logger = logging.getLogger(__name__)


@traced_node(
    "acknowledge",
    snapshot_keys=["session_id", "session_status", "pipeline_status", "customer_phone"],
)
async def acknowledge_node(state: AgentState, db: AsyncIOMotorDatabase) -> dict:
    """
    Node 1: Instantly acknowledges receipt and signals typing to the customer.

    State inputs:  wa_message_id, customer_phone, tenant_id, inbound_text, tenant
    State outputs: session_id, session_status, pipeline_status
    """
    tenant = state["tenant"]
    wa = WhatsAppService()

    try:
        # ── 1a. Mark the customer's message as read (blue ticks) ─────────────
        await wa.mark_as_read(
            phone_number_id=tenant["phone_number_id"],
            wa_message_id=state["wa_message_id"],
            token=tenant["whatsapp_token"],
        )

        # ── 1b. Activate typing indicator (animated dots) ────────────────────
        await wa.send_typing_on(
            phone_number_id=tenant["phone_number_id"],
            customer_phone=state["customer_phone"],
            token=tenant["whatsapp_token"],
        )

        logger.info(f"⌛ Typing indicator ON for {state['customer_phone']}")

    except Exception as e:
        # Don't fail the pipeline if WhatsApp API has issues — just log
        logger.warning(f"⚠️  WhatsApp acknowledge step partial failure: {e}")

    # ── 2. Get or create chat session ─────────────────────────────────────────
    session = await session_repo.get_or_create_session(
        db=db,
        tenant_id=state["tenant_id"],
        customer_phone=state["customer_phone"],
    )
    await session_repo.update_session_status(db, session.id, SessionStatus.AGENT_RESPONDING)

    # ── 3. Save inbound message to audit log ──────────────────────────────────
    inbound_msg = Message(
        session_id=session.id,
        tenant_id=state["tenant_id"],
        direction=MessageDirection.INBOUND,
        sender=state["customer_phone"],
        message_type=MessageType(state.get("inbound_message_type", "text")),
        text_content=state.get("inbound_text"),
        wa_message_id=state["wa_message_id"],
        agent_state_snapshot={"pipeline_status": "PENDING"},
    )
    await message_repo.save_message(db, inbound_msg)
    await session_repo.increment_message_count(db, session.id)

    # ── 4. Log typing_indicator event in DB (for dashboard "was typing" display)
    typing_log = Message(
        session_id=session.id,
        tenant_id=state["tenant_id"],
        direction=MessageDirection.OUTBOUND,
        sender="BOT",
        message_type=MessageType.TYPING_INDICATOR,
        agent_state_snapshot={"pipeline_status": "PROCESSING"},
    )
    await message_repo.save_message(db, typing_log)

    # ── 5. Emit SSE event so dashboard shows "typing..." live ─────────────────
    await broadcast_event(
        tenant_id=state["tenant_id"],
        event_type="typing_on",
        data={
            "session_id": session.id,
            "customer_phone": state["customer_phone"],
        },
    )

    logger.info(f"✅ Acknowledge node complete for session {session.id}")

    return {
        "session_id": session.id,
        "session_status": SessionStatus.AGENT_RESPONDING.value,
        "pipeline_status": "PROCESSING",
    }
