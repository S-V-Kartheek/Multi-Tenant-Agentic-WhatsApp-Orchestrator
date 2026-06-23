"""
utils/security.py — Webhook signature verification.

Validates Twilio's X-Twilio-Signature header to ensure every inbound
webhook POST genuinely originates from Twilio, preventing spoofed requests.

Twilio signs each request with HMAC-SHA1 using your Auth Token as the key.
"""
import hashlib
import hmac
import base64
import logging
from urllib.parse import urlencode, quote
from fastapi import Request, HTTPException

from app.config import get_settings

logger = logging.getLogger(__name__)


async def verify_twilio_signature(request: Request, form_data: dict) -> None:
    """
    Validate the X-Twilio-Signature header on inbound Twilio webhooks.

    Twilio's signing algorithm:
      1. Take the full request URL (including https://)
      2. If POST with form params: sort params alphabetically, append key+value pairs
      3. Sign: HMAC-SHA1(auth_token, url + params)
      4. Base64-encode the result
      5. Compare to X-Twilio-Signature header

    Args:
        request:   The incoming FastAPI request
        form_data: The parsed form fields dict (already read from request)

    Raises:
        HTTPException(403) if signature is missing or invalid
    """
    settings = get_settings()

    # In development mode, skip verification (no HTTPS, local tunnel URL)
    if settings.app_env == "development":
        logger.debug("⚠️  Twilio signature verification skipped in development mode")
        return

    signature_header = request.headers.get("X-Twilio-Signature", "")
    if not signature_header:
        logger.warning("❌ Missing X-Twilio-Signature header")
        raise HTTPException(status_code=403, detail="Missing Twilio webhook signature")

    # Build the string to sign: URL + sorted form params concatenated
    url = str(request.url)
    sorted_params = "".join(
        f"{k}{v}" for k, v in sorted(form_data.items())
    )
    s = url + sorted_params

    # Compute HMAC-SHA1
    expected = base64.b64encode(
        hmac.new(
            key=settings.twilio_auth_token.encode("utf-8"),
            msg=s.encode("utf-8"),
            digestmod=hashlib.sha1,
        ).digest()
    ).decode("utf-8")

    if not hmac.compare_digest(signature_header, expected):
        logger.warning("❌ Twilio signature mismatch — potential spoofed request")
        raise HTTPException(status_code=403, detail="Invalid Twilio webhook signature")

    logger.debug("✅ Twilio webhook signature verified")
