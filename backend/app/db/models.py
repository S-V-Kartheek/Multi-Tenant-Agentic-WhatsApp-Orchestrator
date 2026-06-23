"""
db/models.py — Pydantic data models for all MongoDB collections.

These models serve as the single source of truth for data shapes used in:
  - Database reads/writes (via repositories)
  - API response serialization
  - Agent state construction
"""
from datetime import datetime, timezone
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


# ─── Helpers ──────────────────────────────────────────────────────────────────

def utcnow() -> datetime:
    """Timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class PyObjectId(str):
    """Custom type to handle MongoDB ObjectId serialization in Pydantic v2."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")


# ─── Enums ────────────────────────────────────────────────────────────────────

class SessionStatus(str, Enum):
    WAITING_FOR_BOT = "WAITING_FOR_BOT"
    AGENT_RESPONDING = "AGENT_RESPONDING"
    RESOLVED = "RESOLVED"
    NEEDS_HUMAN = "NEEDS_HUMAN"      # bonus: frustration detected
    AGENT_HANDOFF = "AGENT_HANDOFF"  # human agent has taken over manually


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"
    TYPING_INDICATOR = "typing_indicator"   # logged for dashboard display
    STATUS_UPDATE = "status_update"
    SYSTEM = "system"                       # system / divider events


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    """WhatsApp delivery lifecycle for outbound messages."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class RunStatus(str, Enum):
    """Lifecycle of a single LangGraph agent run."""
    RUNNING = "running"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"


# ─── Tenant ───────────────────────────────────────────────────────────────────

class Tenant(BaseModel):
    """
    Represents a business tenant using the platform.
    Each tenant has their own WhatsApp number, AI persona, and media library.
    """
    id: Optional[str] = Field(None, alias="_id")
    slug: str                               # URL-safe unique name e.g. "luxury-furniture"
    name: str                               # Display name
    phone_number_id: str                    # Meta WhatsApp Phone Number ID
    whatsapp_token: str                     # Meta access token for this tenant
    system_prompt: str                      # AI persona instructions
    media_library: dict[str, str] = {}     # {"catalog": "https://...", "sofa": "https://..."}
    brand_color: str = "#6366F1"           # UI accent color for dashboard
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


class TenantCreate(BaseModel):
    slug: str
    name: str
    phone_number_id: str
    whatsapp_token: str
    system_prompt: str
    media_library: dict[str, str] = {}
    brand_color: str = "#6366F1"


class TenantResponse(BaseModel):
    """Safe tenant response — excludes sensitive tokens."""
    id: str
    slug: str
    name: str
    phone_number_id: str
    system_prompt: str
    media_library: dict[str, str]
    brand_color: str
    created_at: datetime


# ─── Chat Session ─────────────────────────────────────────────────────────────

class ChatSession(BaseModel):
    """
    Represents an ongoing conversation between a customer and the bot.
    One session per (customer_phone, tenant_id) pair.
    """
    id: Optional[str] = Field(None, alias="_id")
    tenant_id: str
    customer_phone: str                         # E.164 format e.g. "+919876543210"
    status: SessionStatus = SessionStatus.WAITING_FOR_BOT
    context_variables: dict[str, Any] = {}    # Arbitrary state for advanced flows
    message_count: int = 0
    last_activity: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    # Agent analytics
    sentiment_score: Optional[float] = None       # last recorded sentiment (0..1)
    resolution_time_sec: Optional[float] = None   # seconds from session open → RESOLVED
    last_run_id: Optional[str] = None             # most recent agent_run _id for quick trace access

    model_config = {"populate_by_name": True}


class ChatSessionResponse(BaseModel):
    id: str
    tenant_id: str
    customer_phone: str
    status: SessionStatus
    message_count: int
    last_activity: datetime
    created_at: datetime
    sentiment_score: Optional[float] = None   # last Gemini sentiment (0=angry, 1=happy)
    last_run_id: Optional[str] = None         # most recent agent_run id for quick trace link


class SessionUpdateRequest(BaseModel):
    """Agent action payload — manual status transitions."""
    status: SessionStatus
    agent_id: Optional[str] = "dashboard_operator"


class SessionStatusUpdateResponse(BaseModel):
    session_id: str
    status: SessionStatus


# ─── Message ──────────────────────────────────────────────────────────────────

class Message(BaseModel):
    """
    Immutable audit log entry for every inbound and outbound message.
    Includes media metadata and a snapshot of agent state at dispatch time.
    """
    id: Optional[str] = Field(None, alias="_id")
    session_id: str
    tenant_id: str
    direction: MessageDirection
    sender: str                            # phone number or "BOT"
    message_type: MessageType
    text_content: Optional[str] = None
    media_url: Optional[str] = None
    media_mime_type: Optional[str] = None  # "image/jpeg", "application/pdf"
    media_filename: Optional[str] = None
    wa_message_id: Optional[str] = None   # Meta's message ID for read receipts
    delivery_status: Optional[str] = MessageStatus.SENT.value  # sent|delivered|read|failed
    agent_state_snapshot: dict = {}        # Snapshot of LangGraph state at this step
    timestamp: datetime = Field(default_factory=utcnow)

    model_config = {"populate_by_name": True}


class MessageResponse(BaseModel):
    id: str
    session_id: str
    direction: MessageDirection
    sender: str
    message_type: MessageType
    text_content: Optional[str]
    media_url: Optional[str]
    media_mime_type: Optional[str]
    media_filename: Optional[str]
    delivery_status: Optional[str] = None
    agent_state_snapshot: dict = {}
    timestamp: datetime


class AgentReplyRequest(BaseModel):
    """Manual reply sent by a human agent from the dashboard."""
    text: str
    agent_id: Optional[str] = "dashboard_operator"


class AgentReplyResponse(BaseModel):
    session_id: str
    message_id: str
    wa_message_id: Optional[str]
    status: SessionStatus


# ─── Agent Run (LangGraph trace) ──────────────────────────────────────────────

class AgentRun(BaseModel):
    """
    A single execution of the LangGraph pipeline for one inbound message.
    Each `steps` entry is a node's snapshot — used by the dashboard
    Run Trace Viewer to visualize state flow through the graph.
    """
    id: Optional[str] = Field(None, alias="_id")
    tenant_id: str
    session_id: str
    customer_phone: str
    inbound_text: Optional[str] = None
    status: RunStatus = RunStatus.RUNNING
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Per-node trace
    steps: list[dict[str, Any]] = []   # [{node, status, started_at, finished_at, duration_ms, snapshot}]

    # Outcome summary
    tool_chosen: Optional[str] = None              # reply_with_text | send_product_image | ...
    response_type: Optional[str] = None            # text | image | document
    sentiment_score: Optional[float] = None
    escalated: bool = False
    error: Optional[str] = None

    model_config = {"populate_by_name": True}


class AgentRunStepResponse(BaseModel):
    node: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    snapshot: dict = {}


class AgentRunResponse(BaseModel):
    id: str
    tenant_id: str
    session_id: str
    customer_phone: str
    inbound_text: Optional[str]
    status: RunStatus
    started_at: datetime
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    steps: list[dict[str, Any]]
    tool_chosen: Optional[str]
    response_type: Optional[str]
    sentiment_score: Optional[float]
    escalated: bool
    error: Optional[str]


# ─── Broadcast Templates & Campaigns ──────────────────────────────────────────

class BroadcastTemplate(BaseModel):
    """A pre-approved WhatsApp template exposed to the dashboard."""
    name: str                        # Meta template name e.g. "new_catalog_promo"
    label: str                       # friendly display label
    category: str                    # MARKETING | UTILITY | AUTHENTICATION
    language: str = "en_US"
    description: str
    body_preview: str                # sample body text for the preview pane


class BroadcastCampaign(BaseModel):
    """A historical record of a broadcast send — powers campaign history view."""
    id: Optional[str] = Field(None, alias="_id")
    tenant_id: str
    template_name: str
    language_code: str = "en_US"
    recipient_count: int
    sent: int
    failed: int
    results: list[dict] = []
    triggered_by: str = "dashboard_operator"
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"populate_by_name": True}


class BroadcastCampaignResponse(BaseModel):
    id: str
    tenant_id: str
    template_name: str
    language_code: str
    recipient_count: int
    sent: int
    failed: int
    created_at: datetime


# ─── Analytics / Metrics ──────────────────────────────────────────────────────

class AgentRunSummary(BaseModel):
    """Compact run summary shown in the Analytics recent-runs table."""
    id: str
    session_id: str
    customer_phone: str
    status: str
    tool_chosen: Optional[str]
    response_type: Optional[str]
    sentiment_score: Optional[float]
    escalated: bool
    duration_ms: Optional[int]
    started_at: str   # ISO string — avoids datetime serialisation issues in dicts


class TenantMetrics(BaseModel):
    """Aggregated KPIs for the analytics dashboard."""
    tenant_id: str
    total_sessions: int
    active_sessions: int
    resolved_sessions: int
    needs_human_sessions: int
    resolution_rate: float                # 0..1
    total_messages: int
    inbound_messages: int
    outbound_messages: int
    broadcasts_sent: int
    avg_resolution_time_sec: Optional[float]
    avg_sentiment: Optional[float]
    status_distribution: dict[str, int]   # {RESOLVED: 12, ...}
    message_type_distribution: dict[str, int]
    hourly_volume: list[dict[str, Any]]   # [{hour: "2024-01-01T10", direction, count}]
    daily_volume: list[dict[str, Any]]    # [{date: "2024-01-01", count: 12}]
    recent_runs: list[AgentRunSummary]    # last 8 agent runs — typed, not raw dicts
