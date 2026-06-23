"""
api/webhooks.py — Twilio WhatsApp webhook handler.

POST /api/webhooks/whatsapp — Inbound message handler (async pattern)

Twilio sends webhook data as application/x-www-form-urlencoded (form data),
unlike Meta which sends JSON. Twilio does NOT use a GET challenge handshake —
it simply POSTs to your URL with each message.

CRITICAL: Return 200 OK (or empty TwiML) to Twilio within 15 seconds.
We achieve this by kicking off LangGraph as a FastAPI BackgroundTask immediately.

Twilio Webhook Fields:
  From         — sender's WhatsApp number e.g. "whatsapp:+919876543210"
  To           — your Twilio sandbox number e.g. "whatsapp:+14155238886"
  Body         — text content of the message
  MessageSid   — unique Twilio message ID (equivalent to Meta's wa_message_id)
  NumMedia     — number of media attachments (0 for text messages)
  MediaUrl0    — URL of first media attachment (if NumMedia > 0)
  MediaContentType0 — MIME type of first attachment
"""
import logging
from fastapi import APIRouter, Request, BackgroundTasks, Depends
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.db.mongo import get_db
from app.db.repositories import tenant_repo

logger = logging.getLogger(__name__)
router = APIRouter()


def extract_message_data(form_data: dict) -> dict | None:
    """
    Parse Twilio's form-encoded webhook payload into a normalized message dict.

    Returns None if:
    - No Body and no media (empty message / status callback)
    - Missing required fields
    """
    try:
        message_sid = form_data.get("MessageSid", "")
        from_number = form_data.get("From", "")        # "whatsapp:+919876543210"
        to_number = form_data.get("To", "")            # "whatsapp:+14155238886"
        body = form_data.get("Body", "").strip()
        num_media = int(form_data.get("NumMedia", 0))
        media_url = form_data.get("MediaUrl0")
        media_mime = form_data.get("MediaContentType0")

        # Normalize: strip the "whatsapp:" prefix for storage
        customer_phone = from_number.replace("whatsapp:", "")
        twilio_number = to_number.replace("whatsapp:", "")

        if not message_sid:
            return None

        # Determine message type
        if num_media > 0 and media_mime:
            if "image" in media_mime:
                message_type = "image"
            elif "pdf" in media_mime or "document" in media_mime:
                message_type = "document"
            else:
                message_type = "image"   # treat unknown media as image
        else:
            message_type = "text"
            if not body:
                return None   # no content at all — skip silently

        return {
            "wa_message_id": message_sid,
            "customer_phone": customer_phone,
            "twilio_number": twilio_number,       # used to route to correct tenant
            "message_type": message_type,
            "text": body if body else None,
            "media_url": media_url,
            "media_mime_type": media_mime,
        }

    except Exception as e:
        logger.warning(f"Failed to parse Twilio webhook payload: {e}")
        return None


@router.post("/webhooks/whatsapp")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Main inbound WhatsApp message handler (Twilio).

    Flow:
    1. Parse Twilio form-data payload
    2. Match to the correct tenant by Twilio number
    3. ✅ Return 200 OK IMMEDIATELY (empty TwiML body — prevents Twilio auto-reply)
    4. LangGraph agent runs in background — fully non-blocking
    """
    # ── Step 1: Parse Twilio form-encoded payload ─────────────────────────────
    try:
        form = await request.form()
        form_data = dict(form)
    except Exception as e:
        logger.warning(f"Failed to read Twilio webhook form data: {e}")
        return Response(content="", media_type="text/xml", status_code=200)

    logger.debug(f"📥 Twilio webhook received: {form_data}")

    message_data = extract_message_data(form_data)

    if not message_data:
        # Not a real user message — acknowledge silently
        return Response(content="", media_type="text/xml", status_code=200)

    # ── Step 2: Match tenant by Twilio 'To' number ────────────────────────────
    # Each tenant in the DB has phone_number_id = their Twilio number (no prefix)
    twilio_number = message_data.get("twilio_number", "")
    settings = get_settings()

    # During sandbox testing, both tenants share the same Twilio number.
    # We default to Tenant A unless the DB explicitly maps this number to Tenant B.
    tenant = None
    all_tenants = await tenant_repo.get_all_tenants(db)

    for t in all_tenants:
        tenant_number = t.phone_number_id.replace("whatsapp:", "")
        if tenant_number == twilio_number:
            tenant = t
            break

    # Fallback: if no exact match found (e.g. single sandbox number), use first tenant
    if not tenant and all_tenants:
        tenant = all_tenants[0]
        logger.info(
            f"ℹ️  No exact tenant match for {twilio_number} — routing to default tenant: {tenant.slug}"
        )

    if not tenant:
        logger.warning("❌ No tenants found in DB — message dropped. Run seed_data.py first.")
        return Response(content="", media_type="text/xml", status_code=200)

    # ── Step 3: ✅ Launch LangGraph as background task — return 200 NOW ───────
    from app.agent.graph import run_agent  # imported here to avoid circular imports

    background_tasks.add_task(
        run_agent,
        message_data=message_data,
        tenant=tenant,
        db=db,
    )

    # Return empty TwiML — tells Twilio "received, no auto-reply needed"
    logger.info(
        f"✅ Webhook accepted | tenant: {tenant.slug} | from: {message_data['customer_phone']}"
    )
    return Response(content="", media_type="text/xml", status_code=200)
