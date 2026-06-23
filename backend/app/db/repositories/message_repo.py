"""
db/repositories/message_repo.py — Data access layer for `messages` collection.

Every inbound and outbound message is written here as an immutable audit log.
This powers the dashboard chat thread and provides LangGraph with conversation history.
"""
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.models import Message, MessageDirection, MessageType, MessageStatus


COLLECTION = "messages"


async def save_message(db: AsyncIOMotorDatabase, message: Message) -> Message:
    """
    Persist a message document to the audit log.
    Returns the saved message with its assigned MongoDB _id.
    """
    doc = message.model_dump(exclude={"id"})
    result = await db[COLLECTION].insert_one(doc)
    message.id = str(result.inserted_id)
    return message


async def get_messages_by_session(
    db: AsyncIOMotorDatabase,
    session_id: str,
    limit: int = 50,
    before_id: str | None = None,
) -> list[Message]:
    """
    Retrieve message history for a chat session (dashboard thread view).
    Sorted ascending so they render oldest-first like a real chat.

    Supports cursor-based pagination via `before_id` for infinite scroll-up.
    """
    query = {"session_id": session_id}
    if before_id:
        query["_id"] = {"$lt": ObjectId(before_id)}

    messages = []
    cursor = (
        db[COLLECTION]
        .find(query)
        .sort("timestamp", -1 if before_id else 1)
        .limit(limit)
    )
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        messages.append(Message(**doc))

    # When paginating backwards we fetched newest→oldest; reverse for display
    if before_id:
        messages.reverse()
    return messages


async def get_recent_messages_for_context(
    db: AsyncIOMotorDatabase,
    session_id: str,
    limit: int = 5,
) -> list[dict]:
    """
    Returns the last N messages as plain dicts for LangGraph context injection.
    Only real text/media messages are included (typing indicators excluded).
    """
    messages = []
    cursor = db[COLLECTION].find(
        {
            "session_id": session_id,
            "message_type": {"$nin": [MessageType.TYPING_INDICATOR.value, MessageType.STATUS_UPDATE.value]},
        }
    ).sort("timestamp", -1).limit(limit)

    async for doc in cursor:
        messages.append({
            "role": "user" if doc["direction"] == MessageDirection.INBOUND.value else "assistant",
            "content": doc.get("text_content") or f"[{doc.get('message_type')} message]",
            "timestamp": doc["timestamp"].isoformat(),
        })

    # Reverse so history is chronological for LLM context
    return list(reversed(messages))


async def get_messages_by_tenant(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
    limit: int = 100,
) -> list[Message]:
    """Fetch recent messages across all sessions for a tenant (analytics view)."""
    messages = []
    cursor = db[COLLECTION].find(
        {"tenant_id": tenant_id}
    ).sort("timestamp", -1).limit(limit)

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        messages.append(Message(**doc))
    return messages


async def get_last_message_preview(
    db: AsyncIOMotorDatabase,
    session_id: str,
) -> str | None:
    """Return a short snippet of the most recent message — for the chat list preview."""
    cursor = (
        db[COLLECTION]
        .find({"session_id": session_id, "message_type": {"$nin": [MessageType.TYPING_INDICATOR.value, MessageType.STATUS_UPDATE.value]}})
        .sort("timestamp", -1)
        .limit(1)
    )
    async for doc in cursor:
        if doc.get("text_content"):
            return doc["text_content"][:60]
        mt = doc.get("message_type", "text")
        return {"image": "📷 Photo", "audio": "🎤 Voice", "video": "🎥 Video", "document": "📄 Document"}.get(mt, f"[{mt}]")
    return None


async def update_delivery_status(
    db: AsyncIOMotorDatabase,
    wa_message_id: str,
    status: MessageStatus,
) -> None:
    """Update the delivery lifecycle of an outbound message (sent → delivered → read)."""
    await db[COLLECTION].update_many(
        {"wa_message_id": wa_message_id},
        {"$set": {"delivery_status": status.value}},
    )


# ─── Aggregations for analytics ───────────────────────────────────────────────

async def get_tenant_message_stats(
    db: AsyncIOMotorDatabase,
    tenant_id: str,
) -> dict:
    """
    Aggregated message counts and distributions for a tenant.
    Returns: {total, inbound, outbound, type_distribution, hourly_volume, daily_volume}
    """
    # Total counts by direction
    inbound = await db[COLLECTION].count_documents({"tenant_id": tenant_id, "direction": "inbound"})
    outbound = await db[COLLECTION].count_documents({"tenant_id": tenant_id, "direction": "outbound"})

    # Type distribution
    type_pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$message_type", "count": {"$sum": 1}}},
    ]
    type_distribution = {}
    async for doc in db[COLLECTION].aggregate(type_pipeline):
        type_distribution[doc["_id"]] = doc["count"]

    # Hourly volume (last 48 hours)
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=48)
    hourly_pipeline = [
        {"$match": {"tenant_id": tenant_id, "timestamp": {"$gte": since}}},
        {"$group": {
            "_id": {
                "hour": {"$dateToString": {"format": "%Y-%m-%dT%H:00:00", "date": "$timestamp"}},
                "direction": "$direction",
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id.hour": 1}},
    ]
    hourly_volume = []
    async for doc in db[COLLECTION].aggregate(hourly_pipeline):
        hourly_volume.append({
            "hour": doc["_id"]["hour"],
            "direction": doc["_id"]["direction"],
            "count": doc["count"],
        })

    # Daily volume (last 14 days)
    since_daily = now - timedelta(days=14)
    daily_pipeline = [
        {"$match": {"tenant_id": tenant_id, "timestamp": {"$gte": since_daily}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    daily_volume = []
    async for doc in db[COLLECTION].aggregate(daily_pipeline):
        daily_volume.append({"date": doc["_id"], "count": doc["count"]})

    return {
        "total": inbound + outbound,
        "inbound": inbound,
        "outbound": outbound,
        "type_distribution": type_distribution,
        "hourly_volume": hourly_volume,
        "daily_volume": daily_volume,
    }
