"""
agent/nodes/dispatcher.py — LangGraph Node 4: Dispatcher.

Final node in the pipeline. Resolves the LLM's decision into a concrete
WhatsApp message and sends it. Then logs the outbound message to MongoDB
and updates session status.

The typing indicator auto-extinguishes when the actual message arrives
on the customer's phone (WhatsApp Cloud API behavior).
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agent.state import AgentState
from app.agent.trace import traced_node
from app.db.models import Message, MessageDirection, MessageType, MessageStatus, SessionStatus
from app.db.repositories import session_repo, message_repo
from app.services.whatsapp import WhatsAppService
from app.services.media_resolver import resolve_media_url, get_filename_from_url
from app.api.sse import broadcast_event
from app.utils.observability import metrics

logger = logging.getLogger(__name__)


@traced_node(
    "dispatcher",
    snapshot_keys=["response_type", "tool_chosen", "sentiment_score", "wa_outbound_message_id", "pipeline_status"],
)
async def dispatcher_node(state: AgentState, db: AsyncIOMotorDatabase) -> dict:
    """
    Node 4: Send the WhatsApp reply and persist the outbound record.

    State inputs:  tenant, customer_phone, response_type, response_text,
                   media_query_term, media_caption, session_id
    State outputs: wa_outbound_message_id, pipeline_status, media_url, media_filename
    """
    tenant = state["tenant"]
    wa = WhatsAppService()
    wa_response = None
    media_url = None
    media_filename = None
    message_type = MessageType.TEXT

    try:
        response_type = state.get("response_type", "text")

        # ── Case 1: Text reply ────────────────────────────────────────────────
        if response_type == "text":
            wa_response = await wa.send_text(
                phone_number_id=tenant["phone_number_id"],
                to=state["customer_phone"],
                text=state.get("response_text", ""),
                token=tenant["whatsapp_token"],
            )
            message_type = MessageType.TEXT

        # ── Case 2: Document (PDF) ────────────────────────────────────────────
        elif response_type == "document":
            query_term = state.get("media_query_term", "")
            media_url = resolve_media_url(
                media_library=tenant.get("media_library", {}),
                query_term=query_term,
            )

            if media_url:
                media_filename = get_filename_from_url(media_url, f"{query_term}.pdf")
                wa_response = await wa.send_document(
                    phone_number_id=tenant["phone_number_id"],
                    to=state["customer_phone"],
                    doc_url=media_url,
                    filename=media_filename,
                    caption=state.get("media_caption", ""),
                    token=tenant["whatsapp_token"],
                )
                message_type = MessageType.DOCUMENT
            else:
                # Fallback to text if media not found
                logger.warning(f"⚠️  No document found for '{query_term}', falling back to text")
                wa_response = await wa.send_text(
                    phone_number_id=tenant["phone_number_id"],
                    to=state["customer_phone"],
                    text=f"{state.get('media_caption', '')}\n\n_(Document not found in our library. Please contact us for more details.)_",
                    token=tenant["whatsapp_token"],
                )

        # ── Case 3: Image ─────────────────────────────────────────────────────
        elif response_type == "image":
            query_term = state.get("media_query_term", "")
            media_url = resolve_media_url(
                media_library=tenant.get("media_library", {}),
                query_term=query_term,
            )

            if media_url:
                wa_response = await wa.send_image(
                    phone_number_id=tenant["phone_number_id"],
                    to=state["customer_phone"],
                    image_url=media_url,
                    caption=state.get("media_caption", ""),
                    token=tenant["whatsapp_token"],
                )
                message_type = MessageType.IMAGE
            else:
                logger.warning(f"⚠️  No image found for '{query_term}', falling back to text")
                wa_response = await wa.send_text(
                    phone_number_id=tenant["phone_number_id"],
                    to=state["customer_phone"],
                    text=f"{state.get('media_caption', '')}\n\n_(Image not found. Please contact us directly.)_",
                    token=tenant["whatsapp_token"],
                )

        # ── Extract outbound message ID from the WhatsApp provider response ──
        # Twilio returns {"sid": "SM...", "status": "queued"}.
        # (Meta Cloud API returns {"messages": [{"id": "..."}]}.)
        wa_message_id = None
        if wa_response:
            if wa_response.get("messages"):
                wa_message_id = wa_response["messages"][0].get("id")
            else:
                wa_message_id = wa_response.get("sid")

    except Exception as e:
        logger.error(f"❌ Dispatcher failed to send message: {e}", exc_info=True)
        return {
            "pipeline_status": "ERROR",
            "error_message": str(e),
        }

    # ── Save outbound message to audit log ────────────────────────────────────
    outbound_msg = Message(
        session_id=state["session_id"],
        tenant_id=state["tenant_id"],
        direction=MessageDirection.OUTBOUND,
        sender="BOT",
        message_type=message_type,
        text_content=state.get("response_text") or state.get("media_caption"),
        media_url=media_url,
        media_mime_type="application/pdf" if message_type == MessageType.DOCUMENT else (
            "image/jpeg" if message_type == MessageType.IMAGE else None
        ),
        media_filename=media_filename,
        wa_message_id=wa_message_id,
        delivery_status=MessageStatus.SENT.value,
        agent_state_snapshot={
            "response_type": response_type,
            "tool_chosen": state.get("tool_chosen"),
            "sentiment_score": state.get("sentiment_score"),
            "pipeline_status": "DONE",
        },
    )
    await message_repo.save_message(db, outbound_msg)
    await session_repo.increment_message_count(db, state["session_id"])

    # ── Cache latest sentiment on the session for analytics ───────────────────
    sentiment = state.get("sentiment_score")
    if sentiment is not None:
        await session_repo.update_session_sentiment(db, state["session_id"], float(sentiment))

    # ── Update session to RESOLVED ────────────────────────────────────────────
    await session_repo.update_session_status(db, state["session_id"], SessionStatus.RESOLVED)

    # ── Emit SSE event to push new message to dashboard ──────────────────────
    await broadcast_event(
        tenant_id=state["tenant_id"],
        event_type="new_message",
        data={
            "session_id": state["session_id"],
            "message_id": outbound_msg.id,
            "customer_phone": state["customer_phone"],
            "message_type": message_type.value,
            "text_content": outbound_msg.text_content,
            "media_url": media_url,
            "direction": "outbound",
            "delivery_status": MessageStatus.SENT.value,
        },
    )
    await broadcast_event(
        tenant_id=state["tenant_id"],
        event_type="session_updated",
        data={
            "session_id": state["session_id"],
            "status": SessionStatus.RESOLVED.value,
        },
    )

    # Observability counters
    metrics.record_message("outbound")

    logger.info(f"✅ Dispatcher complete | type: {response_type} | session: {state['session_id']}")

    return {
        "wa_outbound_message_id": wa_message_id,
        "media_url": media_url,
        "media_filename": media_filename,
        "pipeline_status": "DONE",
    }
