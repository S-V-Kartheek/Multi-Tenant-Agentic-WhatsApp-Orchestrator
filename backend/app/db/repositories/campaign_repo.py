"""
db/repositories/campaign_repo.py — Data access layer for `broadcast_campaigns` collection.

Each document is a historical record of a broadcast send. Powers the
campaign history view in the dashboard.
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.models import BroadcastCampaign


COLLECTION = "broadcast_campaigns"


async def create_campaign(db: AsyncIOMotorDatabase, campaign: BroadcastCampaign) -> BroadcastCampaign:
    """Persist a finished (or in-flight) broadcast campaign record."""
    doc = campaign.model_dump(exclude={"id"})
    result = await db[COLLECTION].insert_one(doc)
    campaign.id = str(result.inserted_id)
    return campaign


async def get_campaigns_by_tenant(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
    limit: int = 25,
) -> list[BroadcastCampaign]:
    """Return campaign history for a tenant (most recent first)."""
    campaigns = []
    cursor = db[COLLECTION].find({"tenant_id": tenant_id}).sort("created_at", -1).limit(limit)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        campaigns.append(BroadcastCampaign(**doc))
    return campaigns


async def count_campaigns_by_tenant(db: AsyncIOMotorDatabase, tenant_id: str) -> int:
    """Total campaigns ever sent by a tenant — for analytics KPIs."""
    return await db[COLLECTION].count_documents({"tenant_id": tenant_id})
