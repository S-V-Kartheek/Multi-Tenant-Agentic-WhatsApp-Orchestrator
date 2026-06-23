"""
db/repositories/session_repo.py — Data access layer for `chat_sessions` collection.

Manages the lifecycle of customer conversation sessions per tenant.
One session is created per unique (customer_phone, tenant_id) pair.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.models import ChatSession, SessionStatus


COLLECTION = "chat_sessions"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_session(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
    customer_phone: str,
) -> ChatSession:
    """
    Retrieve an existing session or create a fresh one.
    Called at the start of every inbound webhook to get context.
    """
    doc = await db[COLLECTION].find_one({
        "tenant_id": tenant_id,
        "customer_phone": customer_phone,
    })

    if doc:
        doc["_id"] = str(doc["_id"])
        return ChatSession(**doc)

    # New customer — create their session
    new_session = ChatSession(
        tenant_id=tenant_id,
        customer_phone=customer_phone,
        status=SessionStatus.WAITING_FOR_BOT,
    )
    result = await db[COLLECTION].insert_one(new_session.model_dump(exclude={"id"}))
    new_session.id = str(result.inserted_id)
    return new_session


async def update_session_status(
    db: AsyncIOMotorDatabase,
    session_id: str,
    status: SessionStatus,
) -> None:
    """Update conversation status and refresh last_activity timestamp."""
    # Compute resolution time when transitioning to RESOLVED
    set_doc: dict = {"status": status.value, "last_activity": utcnow()}

    if status == SessionStatus.RESOLVED:
        session = await db[COLLECTION].find_one({"_id": ObjectId(session_id)})
        if session and session.get("created_at"):
            created = session["created_at"]
            # MongoDB may return a naive datetime (no tz) depending on codec config.
            # Normalize to UTC so the subtraction against the tz-aware utcnow() works.
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            elapsed = (utcnow() - created).total_seconds()
            set_doc["resolution_time_sec"] = round(elapsed, 1)

    await db[COLLECTION].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": set_doc},
    )


async def update_session_sentiment(
    db: AsyncIOMotorDatabase,
    session_id: str,
    sentiment_score: float,
) -> None:
    """Cache the latest sentiment on the session for quick analytics access."""
    await db[COLLECTION].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"sentiment_score": sentiment_score, "last_activity": utcnow()}},
    )


async def set_last_run_id(
    db: AsyncIOMotorDatabase,
    session_id: str,
    run_id: str,
) -> None:
    """Record the most recent agent run on the session for quick trace access."""
    await db[COLLECTION].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"last_run_id": run_id}},
    )


async def increment_message_count(
    db: AsyncIOMotorDatabase,
    session_id: str,
) -> None:
    """Atomically increment the message counter and update last_activity."""
    await db[COLLECTION].update_one(
        {"_id": ObjectId(session_id)},
        {"$inc": {"message_count": 1}, "$set": {"last_activity": utcnow()}},
    )


async def get_sessions_by_tenant(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> list[ChatSession]:
    """
    Fetch active sessions for dashboard display.
    Sorted by last_activity descending (most recent first).

    Optional filters:
      - status: exact status match (e.g. "NEEDS_HUMAN")
      - search: substring match on customer_phone
    """
    query: dict = {"tenant_id": tenant_id}
    if status and status != "ALL":
        query["status"] = status
    if search:
        # Normalize phone search — accept with or without leading '+'
        term = search.strip().lstrip("+")
        query["customer_phone"] = {"$regex": term, "$options": "i"}

    sessions = []
    cursor = db[COLLECTION].find(query).sort("last_activity", -1).limit(limit)

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        sessions.append(ChatSession(**doc))
    return sessions


async def get_session_by_id(
    db: AsyncIOMotorDatabase,
    session_id: str,
) -> ChatSession | None:
    """Fetch a single session by its ID."""
    doc = await db[COLLECTION].find_one({"_id": ObjectId(session_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
        return ChatSession(**doc)
    return None


async def count_sessions_by_status(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
) -> dict[str, int]:
    """Return counts of sessions grouped by status — for analytics KPI cards."""
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    counts: dict[str, int] = {}
    async for doc in db[COLLECTION].aggregate(pipeline):
        counts[doc["_id"]] = doc["count"]
    return counts


async def get_avg_resolution_time(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
) -> Optional[float]:
    """Average seconds-to-resolution across all resolved sessions for a tenant."""
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "resolution_time_sec": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "avg": {"$avg": "$resolution_time_sec"}}},
    ]
    async for doc in db[COLLECTION].aggregate(pipeline):
        return round(doc.get("avg", 0), 1)
    return None


async def get_avg_sentiment(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
) -> Optional[float]:
    """Average sentiment score across a tenant's sessions."""
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "sentiment_score": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "avg": {"$avg": "$sentiment_score"}}},
    ]
    async for doc in db[COLLECTION].aggregate(pipeline):
        return round(doc.get("avg", 0), 2)
    return None
