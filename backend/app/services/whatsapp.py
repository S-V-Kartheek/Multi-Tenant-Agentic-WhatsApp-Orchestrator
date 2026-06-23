"""
services/whatsapp.py — Twilio WhatsApp API helper.

All interactions with the Twilio Messaging API are centralized here.
Uses the official twilio-python SDK for reliable, production-grade messaging.

Replaces the previous Meta Cloud API implementation.
"""
import logging
from typing import Any
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from app.config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Wrapper around the Twilio WhatsApp API.
    Uses the synchronous Twilio SDK.
    """

    def __init__(self):
        settings = get_settings()
        self.client = TwilioClient(
            settings.twilio_account_sid,
            settings.twilio_auth_token,
        )

    def _to_wa(self, phone: str) -> str:
        """
        Ensure phone number has the whatsapp: prefix for Twilio.
        Accepts '+919876543210' or 'whatsapp:+919876543210'.
        """
        if not phone.startswith("whatsapp:"):
            return f"whatsapp:{phone}"
        return phone

    # ── Read Receipt (no-op for Twilio) ──────────────────────────────────────
    async def mark_as_read(
        self, phone_number_id: str, wa_message_id: str, token: str
    ) -> None:
        """
        Twilio sandbox does not support read receipts via API.
        This is a no-op kept for interface compatibility with the agent nodes.
        """
        logger.debug("ℹ️  mark_as_read is not supported by Twilio sandbox — skipped")

    # ── Typing Indicator (no-op for Twilio) ──────────────────────────────────
    async def send_typing_on(
        self, phone_number_id: str, customer_phone: str, token: str
    ) -> None:
        """
        Twilio sandbox does not support typing indicators via API.
        This is a no-op kept for interface compatibility with the agent nodes.
        The dashboard still shows 'typing...' via DB log + SSE (unaffected).
        """
        logger.debug("ℹ️  send_typing_on is not supported by Twilio sandbox — skipped")

    # ── Text Message ──────────────────────────────────────────────────────────
    async def send_text(
        self,
        phone_number_id: str,   # kept for interface compat (unused in Twilio)
        to: str,
        text: str,
        token: str,             # kept for interface compat (unused in Twilio)
        preview_url: bool = False,
    ) -> dict[str, Any]:
        """
        Send a WhatsApp text message via Twilio.
        """
        settings = get_settings()
        from_number = self._get_from_number(phone_number_id, settings)

        try:
            message = self.client.messages.create(
                body=text,
                from_=from_number,
                to=self._to_wa(to),
            )
            logger.info(f"📤 Text message sent to {to} | SID: {message.sid}")
            return {"sid": message.sid, "status": message.status}
        except TwilioRestException as e:
            logger.error(f"❌ Twilio send_text failed: {e}")
            raise

    # ── Image Message ─────────────────────────────────────────────────────────
    async def send_image(
        self,
        phone_number_id: str,
        to: str,
        image_url: str,
        caption: str,
        token: str,
    ) -> dict[str, Any]:
        """
        Send an image with an optional caption via Twilio.
        Twilio sends media via media_url and body as the caption.
        """
        settings = get_settings()
        from_number = self._get_from_number(phone_number_id, settings)

        try:
            message = self.client.messages.create(
                body=caption,
                from_=from_number,
                to=self._to_wa(to),
                media_url=[image_url],
            )
            logger.info(f"🖼️  Image sent to {to} | SID: {message.sid}")
            return {"sid": message.sid, "status": message.status}
        except TwilioRestException as e:
            logger.error(f"❌ Twilio send_image failed: {e}")
            raise

    # ── Document Message ──────────────────────────────────────────────────────
    async def send_document(
        self,
        phone_number_id: str,
        to: str,
        doc_url: str,
        filename: str,
        caption: str,
        token: str,
    ) -> dict[str, Any]:
        """
        Send a PDF or document via Twilio.
        Twilio delivers PDFs as media attachments (body = caption).
        Note: The document URL must be publicly accessible.
        """
        settings = get_settings()
        from_number = self._get_from_number(phone_number_id, settings)

        try:
            message = self.client.messages.create(
                body=f"{caption}\n📎 {filename}",
                from_=from_number,
                to=self._to_wa(to),
                media_url=[doc_url],
            )
            logger.info(f"📄 Document sent to {to}: {filename} | SID: {message.sid}")
            return {"sid": message.sid, "status": message.status}
        except TwilioRestException as e:
            logger.error(f"❌ Twilio send_document failed: {e}")
            raise

    # ── Template / Broadcast Message ──────────────────────────────────────────
    async def send_template(
        self,
        phone_number_id: str,
        to: str,
        template_name: str,
        language_code: str,
        token: str,
        components: list | None = None,
    ) -> dict[str, Any]:
        """
        Broadcast via Twilio — sends a plain-text broadcast message.
        (Twilio sandbox doesn't have Meta-style pre-approved templates,
        so we send the template body text directly.)
        """
        settings = get_settings()
        from_number = self._get_from_number(phone_number_id, settings)

        # Friendly broadcast body using the template name as a label
        broadcast_body = f"📢 {template_name.replace('_', ' ').title()}\n\nThank you for being our valued customer."

        try:
            message = self.client.messages.create(
                body=broadcast_body,
                from_=from_number,
                to=self._to_wa(to),
            )
            logger.info(f"📢 Broadcast '{template_name}' sent to {to} | SID: {message.sid}")
            return {"sid": message.sid, "status": message.status}
        except TwilioRestException as e:
            logger.error(f"❌ Twilio send_template failed: {e}")
            raise

    # ── Helper: resolve from_number by phone_number_id ────────────────────────
    def _get_from_number(self, phone_number_id: str, settings) -> str:
        """
        Map a tenant's phone_number_id field to the Twilio 'from' number.
        During sandbox testing, both tenants use the same Twilio sandbox number.
        phone_number_id is used as a routing key stored in the DB per-tenant.
        """
        if phone_number_id == settings.twilio_whatsapp_number_tenant_b.replace("whatsapp:", ""):
            return settings.twilio_whatsapp_number_tenant_b
        return settings.twilio_whatsapp_number_tenant_a

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass   # Twilio SDK manages its own HTTP session lifecycle
