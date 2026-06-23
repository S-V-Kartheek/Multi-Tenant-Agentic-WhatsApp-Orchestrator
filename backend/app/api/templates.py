"""
api/templates.py — Broadcast templates registry endpoint.

The dashboard fetches the list of approved WhatsApp templates dynamically
so new templates can be registered here without a frontend redeploy.
"""
from fastapi import APIRouter

from app.db.models import BroadcastTemplate
from app.services.templates import get_default_templates

router = APIRouter()


@router.get("/templates", response_model=list[BroadcastTemplate])
async def list_templates():
    """Return all registered broadcast templates."""
    return get_default_templates()
