"""
api/sse.py — Server-Sent Events endpoint for live dashboard updates.

Streams real-time events to the frontend without WebSocket complexity.
The React dashboard subscribes to this endpoint to receive:
  - new_message: A new message was saved for a session
  - session_updated: A session's status changed
  - typing_on: Bot started typing (from acknowledge node)

Events are emitted by the LangGraph agent nodes as they execute.
"""
import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

# In-memory event queue per tenant — keyed by tenant_id
# In production this would be backed by Redis pub/sub for multi-instance support
_subscribers: dict[str, list[asyncio.Queue]] = {}

router = APIRouter()


def get_event_queue(tenant_id: str) -> asyncio.Queue:
    """Create and register a new subscriber queue for a tenant."""
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    if tenant_id not in _subscribers:
        _subscribers[tenant_id] = []
    _subscribers[tenant_id].append(q)
    return q


def remove_event_queue(tenant_id: str, q: asyncio.Queue) -> None:
    """Clean up when a client disconnects."""
    if tenant_id in _subscribers:
        try:
            _subscribers[tenant_id].remove(q)
        except ValueError:
            pass


async def broadcast_event(tenant_id: str, event_type: str, data: dict) -> None:
    """
    Push an event to all connected dashboard clients for a tenant.
    Called from LangGraph agent nodes during execution.
    """
    if tenant_id not in _subscribers:
        return

    event_payload = json.dumps({"type": event_type, "data": data})
    dead_queues = []

    for q in _subscribers[tenant_id]:
        try:
            q.put_nowait(event_payload)
        except asyncio.QueueFull:
            dead_queues.append(q)

    # Remove disconnected clients
    for q in dead_queues:
        remove_event_queue(tenant_id, q)


@router.get("/sse/{tenant_id}")
async def sse_stream(tenant_id: str, request: Request):
    """
    SSE endpoint — frontend subscribes here to receive live updates.
    Connection stays open until the client disconnects.
    """
    q = get_event_queue(tenant_id)

    async def event_generator():
        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'tenant_id': tenant_id})}\n\n"

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait up to 15s for an event, then send keepalive ping
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {event}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive to prevent connection timeout
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"

        finally:
            remove_event_queue(tenant_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # Disable Nginx buffering for SSE
        },
    )
