import asyncio
import json
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.core.redis import subscribe_deals

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sse"])


async def deal_event_generator():
    """Yield SSE events from Redis pub/sub — deals stream in real time."""
    heartbeat_interval = 15
    last_heartbeat = asyncio.get_event_loop().time()

    async for message in subscribe_deals():
        event_type = message.get("event", "new_deal")
        data = message.get("data", {})
        yield {"event": event_type, "data": json.dumps(data)}
        last_heartbeat = asyncio.get_event_loop().time()


async def deal_stream_with_heartbeat():
    """Wraps deal_event_generator with heartbeat pings."""
    heartbeat_task = None
    queue = asyncio.Queue()

    async def push_deals():
        try:
            async for event in deal_event_generator():
                await queue.put(event)
        except asyncio.CancelledError:
            pass

    async def push_heartbeats():
        try:
            while True:
                await asyncio.sleep(15)
                await queue.put({"event": "heartbeat", "data": json.dumps({"status": "alive"})})
        except asyncio.CancelledError:
            pass

    deal_task = asyncio.create_task(push_deals())
    heartbeat_task = asyncio.create_task(push_heartbeats())

    try:
        # Send initial connection event
        yield {"event": "connected", "data": json.dumps({"status": "connected"})}

        while True:
            event = await queue.get()
            yield event
    except asyncio.CancelledError:
        pass
    finally:
        deal_task.cancel()
        heartbeat_task.cancel()


@router.get("/deals/stream")
async def deal_stream():
    return EventSourceResponse(deal_stream_with_heartbeat())
