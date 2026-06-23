"""
api/broadcast.py — Endpoint for sending template broadcast campaigns.

Allows admins to send predefined WhatsApp template messages to a selected
list of customers. Every send is persisted as a BroadcastCampaign record
so the dashboard can show campaign history + analytics.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.db.models import (
    BroadcastCampaign, BroadcastCampaignResponse,
    Message, MessageDirection, MessageType, MessageStatus, SessionStatus,
)
from app.db.repositories import tenant_repo, campaign_repo, session_repo, message_repo
from app.services.whatsapp import WhatsAppService
from app.services.templates import find_template
from app.api.sse import broadcast_event

logger = logging.getLogger(__name__)
router = APIRouter()


class BroadcastRequest(BaseModel):
    tenant_id: str
    template_name: str          # e.g. "new_catalog_promo", "service_reminder"
    phone_numbers: list[str]    # E.164 format numbers to target
    language_code: str = "en_US"
    triggered_by: str = "dashboard_operator"


class BroadcastResponse(BaseModel):
    campaign_id: str
    sent: int
    failed: int
    results: list[dict]


def _campaign_to_response(c: BroadcastCampaign) -> BroadcastCampaignResponse:
    return BroadcastCampaignResponse(
        id=c.id,
        tenant_id=c.tenant_id,
        template_name=c.template_name,
        language_code=c.language_code,
        recipient_count=c.recipient_count,
        sent=c.sent,
        failed=c.failed,
        created_at=c.created_at,
    )


@router.post("/broadcast", response_model=BroadcastResponse)
async def send_broadcast(
    request: BroadcastRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Trigger a WhatsApp template message broadcast to multiple recipients.
    Template must be pre-approved in the Meta Business Manager.
    Persists a campaign record for analytics + history.
    """
    tenant = await tenant_repo.get_tenant_by_id(db, request.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    template = find_template(request.template_name)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown template: {request.template_name}")

    wa = WhatsAppService()
    results: list[dict] = []
    sent = 0
    failed = 0

    for phone in request.phone_numbers:
        # Ensure a chat session exists for this recipient so the broadcast
        # shows up in the Inbox (the dashboard lists rows from chat_sessions).
        # A broadcast is the tenant reaching out first, so the session starts
        # in WAITING_FOR_BOT (no customer reply yet).
        session = await session_repo.get_or_create_session(
            db=db,
            tenant_id=str(tenant.id),
            customer_phone=phone,
        )

        try:
            result = await wa.send_template(
                phone_number_id=tenant.phone_number_id,
                to=phone,
                template_name=request.template_name,
                language_code=request.language_code,
                token=tenant.whatsapp_token,
            )
            # Twilio returns {"sid": "SM...", "status": "queued"}
            wa_sid = result.get("sid")

            # Persist the outbound message so it renders in the chat thread.
            outbound = Message(
                session_id=session.id,
                tenant_id=str(tenant.id),
                direction=MessageDirection.OUTBOUND,
                sender="BOT",
                message_type=MessageType.TEMPLATE,
                text_content=template.body_preview,
                wa_message_id=wa_sid,
                delivery_status=MessageStatus.SENT.value,
                agent_state_snapshot={
                    "source": "broadcast",
                    "template_name": request.template_name,
                    "campaign": True,
                },
            )
            await message_repo.save_message(db, outbound)
            await session_repo.increment_message_count(db, session.id)

            results.append({"phone": phone, "status": "sent", "wa_id": wa_sid, "session_id": session.id})
            sent += 1

            # Push the new message + refreshed session to the dashboard live.
            await broadcast_event(
                tenant_id=str(tenant.id),
                event_type="new_message",
                data={
                    "session_id": session.id,
                    "message_id": outbound.id,
                    "customer_phone": phone,
                    "message_type": MessageType.TEMPLATE.value,
                    "text_content": outbound.text_content,
                    "direction": "outbound",
                    "delivery_status": MessageStatus.SENT.value,
                },
            )
            await broadcast_event(
                tenant_id=str(tenant.id),
                event_type="session_updated",
                data={
                    "session_id": session.id,
                    "status": SessionStatus.WAITING_FOR_BOT.value,
                    "customer_phone": phone,
                },
            )

        except Exception as e:
            logger.warning(f"Broadcast send failed to {phone}: {e}")
            # Still log the attempt so the operator can see the failed send in the thread.
            await message_repo.save_message(db, Message(
                session_id=session.id,
                tenant_id=str(tenant.id),
                direction=MessageDirection.OUTBOUND,
                sender="BOT",
                message_type=MessageType.TEMPLATE,
                text_content=template.body_preview,
                delivery_status=MessageStatus.FAILED.value,
                agent_state_snapshot={
                    "source": "broadcast",
                    "template_name": request.template_name,
                    "error": str(e),
                },
            ))
            await session_repo.increment_message_count(db, session.id)
            results.append({"phone": phone, "status": "failed", "error": str(e), "session_id": session.id})
            failed += 1

    # Persist campaign record
    campaign = BroadcastCampaign(
        tenant_id=request.tenant_id,
        template_name=request.template_name,
        language_code=request.language_code,
        recipient_count=len(request.phone_numbers),
        sent=sent,
        failed=failed,
        results=results,
        triggered_by=request.triggered_by,
    )
    saved = await campaign_repo.create_campaign(db, campaign)

    # Notify dashboard that a new campaign landed (for live campaign history update)
    await broadcast_event(
        tenant_id=request.tenant_id,
        event_type="campaign_created",
        data={
            "campaign_id": saved.id,
            "template_name": request.template_name,
            "sent": sent,
            "failed": failed,
        },
    )

    logger.info(
        f"📢 Broadcast '{request.template_name}' → {sent} sent / {failed} failed "
        f"(campaign {saved.id})"
    )
    return BroadcastResponse(
        campaign_id=saved.id,
        sent=sent,
        failed=failed,
        results=results,
    )


@router.get("/campaigns/{tenant_id}", response_model=list[BroadcastCampaignResponse])
async def get_campaign_history(
    tenant_id: str,
    limit: int = 25,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Return campaign history for a tenant (most recent first)."""
    campaigns = await campaign_repo.get_campaigns_by_tenant(db, tenant_id, limit)
    return [_campaign_to_response(c) for c in campaigns]
