"""
agent/nodes/llm_reasoning.py — LangGraph Node 3: LLM Reasoning.

The brain of the agent. Uses Google Gemini 1.5 Flash with function calling
to determine the appropriate response type (text, image, or document).

Gemini is given 3 tools to call:
  - reply_with_text: plain conversational reply
  - send_catalog_document: PDF from tenant media library
  - send_product_image: Image from tenant media library

Also handles:
  - Bonus: Multimodal image analysis if customer sent an image
  - Bonus: Sentiment scoring for NEEDS_HUMAN detection
"""
import logging
import httpx

import google.generativeai as genai
from app.agent.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Tool Definitions for Gemini Function Calling ──────────────────────────────
AGENT_TOOLS = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="reply_with_text",
                description=(
                    "Send a conversational text reply to the customer. "
                    "Use this for greetings, explanations, follow-up questions, "
                    "or any response that doesn't require a visual media asset."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "text": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="The reply text. Supports WhatsApp markdown (*bold*, _italic_).",
                        ),
                        "sentiment_score": genai.protos.Schema(
                            type=genai.protos.Type.NUMBER,
                            description="Rate the customer's sentiment: 0.0=very frustrated, 1.0=very happy.",
                        ),
                    },
                    required=["text", "sentiment_score"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="send_catalog_document",
                description=(
                    "Send a PDF document from the tenant's media library. "
                    "Use when the customer asks for catalogs, brochures, invoices, "
                    "price lists, spec sheets, or any document asset."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "query_term": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Key term to look up in the media library (e.g. 'catalog', 'invoice', 'brochure').",
                        ),
                        "caption": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Friendly accompanying message to send with the document.",
                        ),
                        "sentiment_score": genai.protos.Schema(
                            type=genai.protos.Type.NUMBER,
                            description="Rate the customer's sentiment: 0.0=very frustrated, 1.0=very happy.",
                        ),
                    },
                    required=["query_term", "caption", "sentiment_score"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="send_product_image",
                description=(
                    "Send an image from the tenant's media library. "
                    "Use when the customer asks to see products, showrooms, repair diagrams, "
                    "or any visual asset."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "query_term": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Key term to look up in the media library (e.g. 'sofa', 'showroom', 'repair').",
                        ),
                        "caption": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Friendly caption to display with the image.",
                        ),
                        "sentiment_score": genai.protos.Schema(
                            type=genai.protos.Type.NUMBER,
                            description="Rate the customer's sentiment: 0.0=very frustrated, 1.0=very happy.",
                        ),
                    },
                    required=["query_term", "caption", "sentiment_score"],
                ),
            ),
        ]
    )
]


async def _download_and_encode_image(media_id: str, token: str) -> bytes | None:
    """
    Download a media file from Meta's API using its media_id.
    Used for multimodal analysis of images sent by the customer (bonus).
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Get the temporary download URL
            url_resp = await client.get(
                f"https://graph.facebook.com/v20.0/{media_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            url_resp.raise_for_status()
            download_url = url_resp.json().get("url")

            # Step 2: Download the actual image bytes
            img_resp = await client.get(
                download_url,
                headers={"Authorization": f"Bearer {token}"},
            )
            img_resp.raise_for_status()
            return img_resp.content
    except Exception as e:
        logger.warning(f"⚠️  Failed to download customer image: {e}")
        return None


async def llm_reasoning_node(state: AgentState) -> dict:
    """
    Node 3: Invoke Gemini with the full conversation context and tool definitions.

    Gemini decides which tool to call based on the customer's intent.
    The tool call arguments become the state updates for the dispatcher node.

    State inputs:  tenant, inbound_text, chat_history, inbound_media_id
    State outputs: response_type, response_text, media_query_term, media_caption,
                   sentiment_score, tool_chosen
    """
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)

    tenant = state["tenant"]

    # ── Build system prompt ───────────────────────────────────────────────────
    media_keys = list(tenant.get("media_library", {}).keys())
    system_prompt = f"""{tenant['system_prompt']}

AVAILABLE MEDIA ASSETS (use the exact key terms when calling media tools):
{', '.join(media_keys) if media_keys else 'No media assets configured.'}

INSTRUCTIONS:
- Always use one of your tools to respond. Never reply with plain text outside a tool call.
- For regular conversation, use reply_with_text.
- If the customer mentions or requests any of the media asset keywords, use the appropriate media tool.
- Be warm, professional, and concise.
- Rate sentiment honestly — 0.25 or below means the customer is frustrated and needs a human agent."""

    # ── Build conversation history for Gemini ─────────────────────────────────
    contents = []
    for msg in state.get("chat_history", []):
        contents.append({
            "role": msg["role"],
            "parts": [{"text": msg["content"]}],
        })

    # ── Handle inbound media (Bonus: multimodal analysis) ─────────────────────
    inbound_parts = []
    if state.get("inbound_media_id") and state.get("inbound_media_mime", "").startswith("image/"):
        img_bytes = await _download_and_encode_image(
            media_id=state["inbound_media_id"],
            token=tenant["whatsapp_token"],
        )
        if img_bytes:
            inbound_parts.append({
                "inline_data": {
                    "mime_type": state["inbound_media_mime"],
                    "data": img_bytes,
                }
            })
            inbound_parts.append({"text": state.get("inbound_text") or "[Customer sent an image]"})
        else:
            inbound_parts.append({"text": state.get("inbound_text") or "[Customer sent an image — could not download]"})
    else:
        inbound_parts.append({"text": state.get("inbound_text", "")})

    contents.append({"role": "user", "parts": inbound_parts})

    # ── Call Gemini with tools ────────────────────────────────────────────────
    # gemini-1.5-flash was deprecated/removed by Google; gemini-2.5-flash is the
    # current Flash model and supports the same function-calling contract.
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt,
        tools=AGENT_TOOLS,
        generation_config=genai.GenerationConfig(temperature=0.7),
    )

    try:
        response = model.generate_content(contents)
        part = response.candidates[0].content.parts[0]

        if not part.function_call:
            # Fallback: if Gemini returned text without a tool call
            logger.warning("⚠️  Gemini returned text without tool call — wrapping as text reply")
            return {
                "response_type": "text",
                "response_text": part.text or "I'm here to help! Could you please clarify your request?",
                "sentiment_score": 0.7,
                "tool_chosen": None,
                "pipeline_status": "PROCESSING",
            }

        # ── Parse the function call ───────────────────────────────────────────
        fn_name = part.function_call.name
        fn_args = dict(part.function_call.args)
        sentiment = float(fn_args.get("sentiment_score", 0.7))

        logger.info(f"🤖 Gemini called tool: {fn_name} | sentiment: {sentiment:.2f}")

        if fn_name == "reply_with_text":
            return {
                "response_type": "text",
                "response_text": fn_args.get("text", ""),
                "sentiment_score": sentiment,
                "tool_chosen": fn_name,
                "pipeline_status": "PROCESSING",
            }

        elif fn_name == "send_catalog_document":
            return {
                "response_type": "document",
                "response_text": fn_args.get("caption", ""),
                "media_query_term": fn_args.get("query_term", ""),
                "media_caption": fn_args.get("caption", ""),
                "sentiment_score": sentiment,
                "tool_chosen": fn_name,
                "pipeline_status": "PROCESSING",
            }

        elif fn_name == "send_product_image":
            return {
                "response_type": "image",
                "response_text": fn_args.get("caption", ""),
                "media_query_term": fn_args.get("query_term", ""),
                "media_caption": fn_args.get("caption", ""),
                "sentiment_score": sentiment,
                "tool_chosen": fn_name,
                "pipeline_status": "PROCESSING",
            }

        else:
            raise ValueError(f"Unknown tool: {fn_name}")

    except Exception as e:
        logger.error(f"❌ LLM reasoning failed: {e}", exc_info=True)
        return {
            "response_type": "text",
            "response_text": "I'm sorry, I'm having trouble right now. Please try again in a moment.",
            "sentiment_score": 0.5,
            "tool_chosen": None,
            "pipeline_status": "ERROR",
            "error_message": str(e),
        }
