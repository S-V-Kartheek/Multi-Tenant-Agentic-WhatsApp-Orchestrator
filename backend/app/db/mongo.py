"""
db/mongo.py — Motor async MongoDB client.

Provides a single shared AsyncIOMotorClient instance across the app lifetime.
Collections are accessed via get_db() dependency injection in FastAPI routes.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

# Module-level client — initialized once on app startup
_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Called during FastAPI lifespan startup to open the MongoDB connection."""
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_uri)
    # Ping to verify connection is alive
    await _client.admin.command("ping")
    print(f"[OK] MongoDB connected: {settings.mongo_db_name}")


async def close_db() -> None:
    """Called during FastAPI lifespan shutdown to gracefully close connection."""
    global _client
    if _client:
        _client.close()
        print("[OK] MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency — returns the active database handle.
    Raises RuntimeError if called before connect_db().
    """
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized. Call connect_db() first.")
    settings = get_settings()
    return _client[settings.mongo_db_name]
