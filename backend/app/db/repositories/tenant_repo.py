"""
db/repositories/tenant_repo.py — Data access layer for the `tenants` collection.

All DB operations are isolated here so the rest of the app never
touches raw MongoDB queries directly (clean separation of concerns).
"""
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.models import Tenant, TenantCreate


COLLECTION = "tenants"


async def create_tenant(db: AsyncIOMotorDatabase, data: TenantCreate) -> Tenant:
    """Insert a new tenant document and return the created record."""
    doc = data.model_dump()
    result = await db[COLLECTION].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return Tenant(**doc)


async def get_tenant_by_id(db: AsyncIOMotorDatabase, tenant_id: str) -> Tenant | None:
    """Fetch a tenant by MongoDB ObjectId string."""
    doc = await db[COLLECTION].find_one({"_id": ObjectId(tenant_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
        return Tenant(**doc)
    return None


async def get_tenant_by_slug(db: AsyncIOMotorDatabase, slug: str) -> Tenant | None:
    """Fetch a tenant by their URL-safe slug (e.g. 'luxury-furniture')."""
    doc = await db[COLLECTION].find_one({"slug": slug})
    if doc:
        doc["_id"] = str(doc["_id"])
        return Tenant(**doc)
    return None


async def get_all_tenants(db: AsyncIOMotorDatabase) -> list[Tenant]:
    """Return all tenants — used by the dashboard tenant switcher."""
    tenants = []
    async for doc in db[COLLECTION].find():
        doc["_id"] = str(doc["_id"])
        tenants.append(Tenant(**doc))
    return tenants


async def upsert_tenant(db: AsyncIOMotorDatabase, data: TenantCreate) -> Tenant:
    """Insert or update a tenant by slug — used by seed script."""
    doc = data.model_dump()
    result = await db[COLLECTION].find_one_and_update(
        {"slug": data.slug},
        {"$set": doc},
        upsert=True,
        return_document=True,
    )
    result["_id"] = str(result["_id"])
    return Tenant(**result)
