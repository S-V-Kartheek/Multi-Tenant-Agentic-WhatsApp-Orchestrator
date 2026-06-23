"""
agent/state.py — LangGraph AgentState definition.

This TypedDict is the single shared state object that flows through
all 4 nodes of the LangGraph pipeline. Each node reads from and writes
to this state — LangGraph handles merging between nodes.
"""
from typing import Optional, Literal, Any
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state object for the WhatsApp agent pipeline.

    Flows through nodes in order:
      Acknowledge → Context Retriever → LLM Reasoning → Dispatcher

    Each node may add or update fields. LangGraph merges state automatically.
    `total=False` lets nodes return partial updates without re-declaring every key.
    """

    # ── Run trace ─────────────────────────────────────────────────────────────
    run_id: Optional[str]                  # MongoDB _id of the agent_run trace document

    # ── Inbound Message ───────────────────────────────────────────────────────
    wa_message_id: str                    # Meta's unique message ID (for read receipt)
    customer_phone: str                   # E.164 format e.g. "+919876543210"
    tenant_id: str                        # MongoDB ObjectId string of the tenant
    inbound_text: Optional[str]           # Customer's text message body
    inbound_message_type: str             # "text", "image", "document", etc.

    # ── Inbound Media (Bonus: multimodal parsing) ─────────────────────────────
    inbound_media_id: Optional[str]       # Meta media ID if customer sent image
    inbound_media_mime: Optional[str]     # MIME type of the customer's media
    inbound_media_description: Optional[str]  # Gemini's description of the image

    # ── Tenant Context (populated by Context Retriever node) ─────────────────
    tenant: Optional[dict]               # Full tenant document from MongoDB
    chat_history: list[dict]             # Last 5 messages as [{role, content}]
    session_id: Optional[str]            # MongoDB session _id
    session_status: str                  # Current session status

    # ── LLM Decision (populated by LLM Reasoning node) ───────────────────────
    response_type: Optional[Literal["text", "image", "document"]]
    response_text: Optional[str]         # Bot's text reply
    media_query_term: Optional[str]      # Term to look up in media_library
    media_caption: Optional[str]         # Caption for image/document
    tool_chosen: Optional[str]           # Name of the Gemini function called

    # ── Resolved Media (populated by Dispatcher node) ─────────────────────────
    media_url: Optional[str]             # Resolved public URL from media_library
    media_filename: Optional[str]        # Filename for document messages

    # ── Sentiment & Safety (Bonus: NEEDS_HUMAN fallover) ─────────────────────
    sentiment_score: Optional[float]     # 0.0 (frustrated) → 1.0 (happy)

    # ── Flow Control ──────────────────────────────────────────────────────────
    pipeline_status: str                 # PENDING | PROCESSING | DONE | NEEDS_HUMAN | ERROR
    error_message: Optional[str]         # Set if an exception occurs in any node
    wa_outbound_message_id: Optional[str]  # Meta's ID for the outbound reply
