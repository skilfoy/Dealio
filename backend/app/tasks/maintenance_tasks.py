"""Maintenance tasks: expire deals, clean history."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import update, delete

from app.models.deal import Deal
from app.models.price_history import PriceHistory
from app.core.database import async_session
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.maintenance_tasks.expire_old_deals")
def expire_old_deals():
    """Mark deals older than 48 hours as inactive."""

    async def _expire():
        async with async_session() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
            result = await db.execute(
                update(Deal)
                .where(Deal.is_active == True, Deal.last_seen_at < cutoff)
                .values(is_active=False)
            )
            await db.commit()
            count = result.rowcount
            logger.info("Expired %d old deals", count)
            return count

    return _run_async(_expire())


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_price_history")
def cleanup_price_history():
    """Delete price history older than 1 year."""

    async def _cleanup():
        async with async_session() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=365)
            result = await db.execute(
                delete(PriceHistory).where(PriceHistory.recorded_at < cutoff)
            )
            await db.commit()
            count = result.rowcount
            logger.info("Cleaned up %d old price history records", count)
            return count

    return _run_async(_cleanup())
