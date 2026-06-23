"""
agent/graph.py — LangGraph stateful graph definition.

Wires all 4 nodes into a directed graph with conditional edges:

  [START]
     │
     ▼
  Acknowledge Node          ── fires read receipt + typing indicator
     │
     ▼
  Context Retriever Node    ── loads tenant config + chat history
     │
     ▼
  LLM Reasoning Node        ── Gemini decides: text | image | document
     │
     ├── sentiment < 0.25 ──► Needs Human Node ──► [END]
     │
     └── normal ────────────► Dispatcher Node ──► [END]

The run_agent() function is the entry point called from the webhook handler.
It also creates an AgentRun trace document and records each node's step so the
dashboard Run Trace Viewer can visualize the full state flow.
"""
import logging
from functools import partial

from langgraph.graph import StateGraph, END
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agent.state import AgentState
from app.agent.nodes.acknowledge import acknowledge_node
from app.agent.nodes.context_retriever import context_retriever_node
from app.agent.nodes.llm_reasoning import llm_reasoning_node
from app.agent.nodes.dispatcher import dispatcher_node
from app.agent.trace import record_step
from app.db.models import AgentRun, RunStatus, SessionStatus
from app.db.repositories import session_repo, agent_run_repo
from app.services.whatsapp import WhatsAppService
from app.api.sse import broadcast_event
from app.utils.observability import metrics

logger = logging.getLogger(__name__)

# Frustration threshold — below this score, route to NEEDS_HUMAN
SENTIMENT_THRESHOLD = 0.25


def should_escalate(state: AgentState) -> str:
    """
    Conditional edge function: route based on customer sentiment.

    Returns:
        "needs_human" if LLM detected frustration (score < threshold)
        "dispatcher"  for normal flow
    """
    score = state.get("sentiment_score", 1.0)
    if score is not None and score < SENTIMENT_THRESHOLD:
        logger.warning(
            f"🔴 Low sentiment detected ({score:.2f}) for {state['customer_phone']} "
            f"— escalating to NEEDS_HUMAN"
        )
        return "needs_human"
    return "dispatcher"


async def _trace_llm_step(db: AsyncIOMotorDatabase, state_before: AgentState, state_after: dict) -> None:
    """Record the LLM reasoning step (node has no db access, so we trace it from the wrapper)."""
    merged = {**state_before, **(state_after or {})}
    await record_step(
        db=db,
        state=merged,
        node="llm_reasoning",
        status="completed",
        snapshot_keys=["response_type", "tool_chosen", "sentiment_score", "pipeline_status"],
    )


def build_graph(db: AsyncIOMotorDatabase) -> StateGraph:
    """
    Construct and compile the LangGraph pipeline.

    We use functools.partial to inject the DB dependency into nodes
    since LangGraph nodes only receive `state` as their argument.

    The LLM node is wrapped so its trace step is recorded against the shared
    db handle (the raw node only takes `state`).
    """
    async def llm_reasoning_traced(state: AgentState) -> dict:
        update = await llm_reasoning_node(state)
        # Record the trace step using the graph-level db handle
        await _trace_llm_step(db, state, update)
        return update

    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("acknowledge", partial(acknowledge_node, db=db))
    graph.add_node("context_retriever", partial(context_retriever_node, db=db))
    graph.add_node("llm_reasoning", llm_reasoning_traced)
    graph.add_node("dispatcher", partial(dispatcher_node, db=db))
    graph.add_node("needs_human", partial(needs_human_node, db=db))

    # ── Define edges ──────────────────────────────────────────────────────────
    graph.set_entry_point("acknowledge")
    graph.add_edge("acknowledge", "context_retriever")
    graph.add_edge("context_retriever", "llm_reasoning")

    # Conditional edge after LLM reasoning — normal vs escalation
    graph.add_conditional_edges(
        "llm_reasoning",
        should_escalate,
        {
            "dispatcher": "dispatcher",
            "needs_human": "needs_human",
        },
    )

    graph.add_edge("dispatcher", END)
    graph.add_edge("needs_human", END)

    return graph.compile()


async def needs_human_node(state: AgentState, db: AsyncIOMotorDatabase) -> dict:
    """
    Bonus: NEEDS_HUMAN escalation node.

    When sentiment is critically low, halt auto-replies and flag the session
    so a human agent can take over. Emits SSE event to highlight in red on dashboard.
    """
    from datetime import datetime, timezone

    tenant = state["tenant"]
    wa = WhatsAppService()

    # Notify the customer that a human will be in touch
    empathy_message = (
        "I'm sorry to hear you're having difficulties. 😔 "
        "I'm connecting you with one of our team members right away. "
        "They'll be in touch with you very shortly!"
    )

    try:
        await wa.send_text(
            phone_number_id=tenant["phone_number_id"],
            to=state["customer_phone"],
            text=empathy_message,
            token=tenant["whatsapp_token"],
        )
    except Exception as e:
        logger.warning(f"⚠️  Could not send escalation message: {e}")

    # Update session status to NEEDS_HUMAN (stops further auto-replies)
    if state.get("session_id"):
        await session_repo.update_session_status(
            db, state["session_id"], SessionStatus.NEEDS_HUMAN
        )
        sentiment = state.get("sentiment_score")
        if sentiment is not None:
            await session_repo.update_session_sentiment(db, state["session_id"], float(sentiment))

    # Log the empathy message + system escalation marker to the audit trail
    if state.get("session_id"):
        from app.db.models import Message, MessageDirection, MessageType
        from app.db.repositories import message_repo
        await message_repo.save_message(db, Message(
            session_id=state["session_id"],
            tenant_id=state["tenant_id"],
            direction=MessageDirection.OUTBOUND,
            sender="BOT",
            message_type=MessageType.TEXT,
            text_content=empathy_message,
            agent_state_snapshot={"pipeline_status": "NEEDS_HUMAN", "escalated": True},
        ))
        await session_repo.increment_message_count(db, state["session_id"])
        await message_repo.save_message(db, Message(
            session_id=state["session_id"],
            tenant_id=state["tenant_id"],
            direction=MessageDirection.OUTBOUND,
            sender="SYSTEM",
            message_type=MessageType.SYSTEM,
            text_content=f"[Escalated to NEEDS_HUMAN — sentiment {state.get('sentiment_score'):.2f}]",
            agent_state_snapshot={"escalated": True, "sentiment_score": state.get("sentiment_score")},
        ))

    # Record this node in the trace
    await record_step(
        db=db,
        state=state,
        node="needs_human",
        status="escalated",
        snapshot_keys=["sentiment_score", "pipeline_status", "session_id"],
    )

    # Emit SSE event to highlight this session in RED on dashboard
    await broadcast_event(
        tenant_id=state["tenant_id"],
        event_type="session_updated",
        data={
            "session_id": state["session_id"],
            "status": SessionStatus.NEEDS_HUMAN.value,
            "customer_phone": state["customer_phone"],
            "sentiment_score": state.get("sentiment_score"),
        },
    )

    logger.warning(
        f"🔴 Session {state['session_id']} escalated to NEEDS_HUMAN "
        f"(sentiment: {state.get('sentiment_score', 'N/A')})"
    )

    return {"pipeline_status": "NEEDS_HUMAN"}


async def run_agent(
    message_data: dict,
    tenant: object,
    db: AsyncIOMotorDatabase,
) -> None:
    """
    Entry point called from the webhook BackgroundTask.

    Constructs the initial AgentState, creates an AgentRun trace document, runs
    the compiled LangGraph pipeline, and stamps the final outcome on the trace.

    All errors are caught here so background task failures don't crash the server.

    Args:
        message_data: Parsed fields from the Meta webhook payload
        tenant: Tenant document from MongoDB
        db: Async Motor database handle
    """
    from datetime import datetime, timezone

    # Resolve session first so the run document can reference it
    session = await session_repo.get_or_create_session(
        db=db,
        tenant_id=str(tenant.id),
        customer_phone=message_data["customer_phone"],
    )

    # ── Create the agent run trace document ───────────────────────────────────
    run = AgentRun(
        tenant_id=str(tenant.id),
        session_id=session.id,
        customer_phone=message_data["customer_phone"],
        inbound_text=message_data.get("text"),
        status=RunStatus.RUNNING,
    )
    run = await agent_run_repo.create_run(db, run)
    await session_repo.set_last_run_id(db, session.id, run.id)

    try:
        # Build the initial state with all inbound data
        initial_state: AgentState = {
            # Trace
            "run_id": run.id,
            # Inbound
            "wa_message_id": message_data["wa_message_id"],
            "customer_phone": message_data["customer_phone"],
            "tenant_id": str(tenant.id),
            "inbound_text": message_data.get("text"),
            "inbound_message_type": message_data.get("message_type", "text"),
            "inbound_media_id": message_data.get("media_url"),    # Twilio sends URL directly (not ID like Meta)
            "inbound_media_mime": message_data.get("media_mime_type"),
            "inbound_media_description": None,
            # Context (populated by nodes)
            "tenant": {
                "_id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "phone_number_id": tenant.phone_number_id,
                "whatsapp_token": tenant.whatsapp_token,
                "system_prompt": tenant.system_prompt,
                "media_library": tenant.media_library,
                "brand_color": tenant.brand_color,
            },
            "chat_history": [],
            "session_id": session.id,
            "session_status": session.status.value,
            # LLM outputs (populated by nodes)
            "response_type": None,
            "response_text": None,
            "media_query_term": None,
            "media_caption": None,
            "tool_chosen": None,
            "media_url": None,
            "media_filename": None,
            "sentiment_score": None,
            # Control
            "pipeline_status": "PENDING",
            "error_message": None,
            "wa_outbound_message_id": None,
        }

        # Build and run the compiled graph
        graph = build_graph(db)
        final_state = await graph.ainvoke(initial_state)

        pipeline_status = final_state.get("pipeline_status")
        escalated = pipeline_status == "NEEDS_HUMAN"

        # ── Stamp final outcome on the run trace ─────────────────────────────
        run_status = RunStatus.ESCALATED if escalated else (
            RunStatus.FAILED if pipeline_status == "ERROR" else RunStatus.COMPLETED
        )
        await agent_run_repo.complete_run(
            db=db,
            run_id=run.id,
            status=run_status,
            tool_chosen=final_state.get("tool_chosen"),
            response_type=final_state.get("response_type"),
            sentiment_score=(
                float(final_state["sentiment_score"])
                if final_state.get("sentiment_score") is not None else None
            ),
            escalated=escalated,
            error=final_state.get("error_message"),
        )

        metrics.record_agent_run(run_status.value)
        metrics.record_message("inbound")

        logger.info(
            f"✅ Agent pipeline complete | status: {pipeline_status} "
            f"| phone: {message_data['customer_phone']} | run: {run.id}"
        )

    except Exception as e:
        logger.error(
            f"❌ Agent pipeline crashed for {message_data.get('customer_phone')}: {e}",
            exc_info=True,
        )
        # Mark the run as failed so the trace reflects the crash
        try:
            await agent_run_repo.complete_run(
                db=db, run_id=run.id, status=RunStatus.FAILED, error=str(e),
            )
            metrics.record_agent_run("failed")
        except Exception:
            pass
