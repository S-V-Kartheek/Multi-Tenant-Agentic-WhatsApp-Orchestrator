"""
services/templates.py — Registry of pre-approved WhatsApp broadcast templates.

These names MUST match templates approved in the Meta Business Manager.
The dashboard fetches this list dynamically so new templates can be added
without a frontend redeploy.
"""
from app.db.models import BroadcastTemplate


# ── Default registry (shared across tenants) ──────────────────────────────────
# In production each entry corresponds to an approved template in Meta Business Manager.
DEFAULT_TEMPLATES: list[BroadcastTemplate] = [
    BroadcastTemplate(
        name="new_catalog_promo",
        label="📦 New Catalog Promo",
        category="MARKETING",
        language="en_US",
        description="Announce a new product catalog launch to opted-in customers.",
        body_preview="Hi {{1}}! 🛋️ Our brand-new 2024 catalog just dropped. Tap below to explore the full collection.",
    ),
    BroadcastTemplate(
        name="service_reminder",
        label="🔧 Service Reminder",
        category="UTILITY",
        language="en_US",
        description="Remind customers about an upcoming or due scheduled service.",
        body_preview="Hi {{1}}, this is a friendly reminder that your vehicle service is due on {{2}}. Reply to book a slot.",
    ),
    BroadcastTemplate(
        name="seasonal_offer",
        label="🏷️ Seasonal Offer",
        category="MARKETING",
        language="en_US",
        description="Promote seasonal discounts and limited-time deals.",
        body_preview="✨ {{1}}, our seasonal sale is live! Enjoy up to {{2}}% off premium pieces this week only.",
    ),
    BroadcastTemplate(
        name="appointment_confirm",
        label="✅ Appointment Confirmation",
        category="UTILITY",
        language="en_US",
        description="Confirm an upcoming appointment with date and time.",
        body_preview="Hi {{1}}! Your appointment is confirmed for {{2}} at {{3}}. See you soon! 🚗",
    ),
    BroadcastTemplate(
        name="feedback_request",
        label="⭐ Feedback Request",
        category="UTILITY",
        language="en_US",
        description="Ask a customer for feedback after a resolved conversation.",
        body_preview="Hi {{1}}, how did we do today? Tap a star to rate your experience 💬",
    ),
]


def get_default_templates() -> list[BroadcastTemplate]:
    """Return all registered default templates."""
    return DEFAULT_TEMPLATES


def find_template(name: str) -> BroadcastTemplate | None:
    """Look up a template by its Meta name."""
    for t in DEFAULT_TEMPLATES:
        if t.name == name:
            return t
    return None
