"""
test_webhook.py — Local end-to-end test script.

Simulates an inbound Twilio WhatsApp webhook POST to the local backend.
This lets you test the full LangGraph pipeline without needing ngrok.

Usage:
    python test_webhook.py "Hello, can I see your catalog?"
    python test_webhook.py "Send me a sofa image"
    python test_webhook.py "Show me the invoice"
"""
import sys
import os
import httpx
import asyncio

BACKEND_URL = "http://localhost:8080"

# Simulated Twilio webhook payload (form-encoded)
TEST_PHONE = "+919876543210"  # Customer's phone (change to your real number)
TWILIO_SANDBOX_NUMBER = "+14155238886"
TEST_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC_TEST_ACCOUNT_SID")

async def simulate_inbound(message: str, phone: str = TEST_PHONE):
    """POST a simulated Twilio webhook to the local backend."""
    payload = {
        "MessageSid": "SMtest12345678",
        "From": f"whatsapp:{phone}",
        "To": f"whatsapp:{TWILIO_SANDBOX_NUMBER}",
        "Body": message,
        "NumMedia": "0",
        "AccountSid": TEST_ACCOUNT_SID,
        "ApiVersion": "2010-04-01",
        "SmsStatus": "received",
    }

    print(f"\n{'='*60}")
    print(f"  Simulating Twilio webhook:")
    print(f"  From: {phone}")
    print(f"  Message: \"{message}\"")
    print(f"{'='*60}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/webhooks/whatsapp",
            data=payload,   # form-encoded, same as Twilio
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    print(f"\n  Backend response: {resp.status_code} {resp.text[:100]}")

    if resp.status_code == 200:
        print(f"\n  [OK] Webhook accepted! LangGraph is processing in background.")
        print(f"       Check the backend logs for the full agent pipeline trace.")
        print(f"       The Gemini AI response will be sent via Twilio to {phone}")
        print(f"       (only if {phone} has joined your Twilio sandbox)")
    else:
        print(f"\n  [ERROR] Unexpected status: {resp.status_code}")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Hello! What can you do?"
    asyncio.run(simulate_inbound(msg))
