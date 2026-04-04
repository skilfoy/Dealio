import json
import logging
from typing import AsyncGenerator

import redis as sync_redis
import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_async_redis = None
_sync_redis = None


async def get_async_redis() -> aioredis.Redis:
    global _async_redis
    if _async_redis is None:
        _async_redis = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _async_redis


def get_sync_redis() -> sync_redis.Redis:
    global _sync_redis
    if _sync_redis is None:
        _sync_redis = sync_redis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _sync_redis


async def publish_deal(deal_data: dict) -> None:
    r = await get_async_redis()
    await r.publish("deals:new", json.dumps({"event": "new_deal", "data": deal_data}))


async def publish_scan_progress(retailer_name: str, items_found: int, deals_found: int) -> None:
    r = await get_async_redis()
    await r.publish(
        "deals:new",
        json.dumps(
            {
                "event": "scan_progress",
                "data": {
                    "retailer": retailer_name,
                    "items_found": items_found,
                    "deals_found": deals_found,
                },
            }
        ),
    )


def publish_deal_sync(deal_data: dict) -> None:
    r = get_sync_redis()
    r.publish("deals:new", json.dumps({"event": "new_deal", "data": deal_data}))


def publish_scan_progress_sync(retailer_name: str, items_found: int, deals_found: int) -> None:
    r = get_sync_redis()
    r.publish(
        "deals:new",
        json.dumps(
            {
                "event": "scan_progress",
                "data": {
                    "retailer": retailer_name,
                    "items_found": items_found,
                    "deals_found": deals_found,
                },
            }
        ),
    )


async def subscribe_deals() -> AsyncGenerator[dict, None]:
    r = await get_async_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe("deals:new")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    yield json.loads(message["data"])
                except json.JSONDecodeError:
                    continue
    finally:
        await pubsub.unsubscribe("deals:new")
        await pubsub.close()
