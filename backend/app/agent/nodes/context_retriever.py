"""
agent/nodes/context_retriever.py — LangGraph Node 2: Context Retriever.

Pulls everything the LLM needs to craft an intelligent, personalized response:
  - The tenant's system prompt and media library
  - The last 5 messages of conversation history
  - Current session metadata

This node bridges the database and the LLM reasoning layer.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agent.state import AgentState
from app.agent.trace import traced_node
from app.db.repositories import message_repo

logger = logging.getLogger(__name__)


@traced_node(
    "context_retriever",
    snapshot_keys=["session_id", "chat_history"],
)
async def context_retriever_node(state: AgentState, db: AsyncIOMotorDatabase) -> dict:
    """
    Node 2: Loads tenant configuration and chat history from MongoDB.

    State inputs:  tenant_id, session_id, tenant (already set from webhook routing)
    State outputs: chat_history (last 5 messages as LLM-ready dicts)
    """
    session_id = state.get("session_id")

    # ── Fetch last 5 messages for conversation context ────────────────────────
    # Returns [{role: "user"|"assistant", content: str, timestamp: str}]
    chat_history = []
    if session_id:
        chat_history = await message_repo.get_recent_messages_for_context(
            db=db,
            session_id=session_id,
            limit=5,
        )

    logger.info(
        f"📚 Context loaded | tenant: {state['tenant']['name']} | "
        f"history: {len(chat_history)} messages"
    )

    return {
        "chat_history": chat_history,
    }
