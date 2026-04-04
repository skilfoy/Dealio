"""Celery tasks for scraping retailers."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session
from app.core.redis import publish_scan_progress_sync
from app.core.security import decrypt_api_key
from app.models.api_key import ApiKey
from app.models.retailer import Retailer
from app.tasks.celery_app import celery_app

# Import all scrapers to trigger registration
from app.scrapers import (  # noqa: F401
    bestbuy, target, walmart, amazon, slickdeals, dealnews, woot,  # Tier 1
    newegg, bh_photo, home_depot, costco, gamestop, dell, lenovo, staples,  # Tier 2
    doordash, apple_refurb, bestbuy_outlet, dell_outlet, keepa, rainforest, microsoft_store,  # Tier 3
)
from app.scrapers.registry import get_scraper, get_all_scrapers

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async code from sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_api_key_for_retailer(db: AsyncSession, retailer: Retailer) -> str | None:
    if not retailer.api_key_service:
        return None
    result = await db.execute(
        select(ApiKey).where(ApiKey.service_slug == retailer.api_key_service)
    )
    key = result.scalars().first()
    if key and key.encrypted_key:
        return decrypt_api_key(key.encrypted_key)
    return None


@celery_app.task(name="app.tasks.scrape_tasks.scrape_retailer", bind=True, max_retries=2)
def scrape_retailer(self, slug: str):
    """Scrape a single retailer by slug."""
    logger.info("Starting scrape for: %s", slug)

    async def _do_scrape():
        async with async_session() as db:
            result = await db.execute(select(Retailer).where(Retailer.slug == slug))
            retailer = result.scalars().first()
            if not retailer:
                logger.error("Retailer not found: %s", slug)
                return {"error": f"Retailer {slug} not found"}

            if not retailer.is_enabled:
                logger.info("Retailer %s is disabled, skipping", slug)
                return {"skipped": True}

            scraper_cls = get_scraper(slug)
            if not scraper_cls:
                logger.warning("No scraper registered for: %s", slug)
                return {"error": f"No scraper for {slug}"}

            # Get API key if needed
            api_key = await _get_api_key_for_retailer(db, retailer)
            if retailer.requires_api_key and not api_key:
                logger.info("Skipping %s — requires API key", slug)
                return {"skipped": True, "reason": "api_key_required"}

            scraper = scraper_cls(db=db, api_key=api_key)
            scrape_result = await scraper.run()

            # Publish progress
            publish_scan_progress_sync(
                retailer.name,
                scrape_result.items_found,
                scrape_result.deals_found,
            )

            logger.info(
                "Scrape complete for %s: %d items, %d deals",
                slug, scrape_result.items_found, scrape_result.deals_found,
            )
            return {
                "retailer": slug,
                "items_found": scrape_result.items_found,
                "deals_found": scrape_result.deals_found,
                "errors": scrape_result.errors[:5],
            }

    try:
        return _run_async(_do_scrape())
    except Exception as e:
        logger.error("Scrape task failed for %s: %s", slug, e)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="app.tasks.scrape_tasks.scrape_tier")
def scrape_tier(tier: int):
    """Scrape all enabled retailers of a given tier."""
    logger.info("Starting tier %d scrape", tier)

    async def _get_slugs():
        async with async_session() as db:
            result = await db.execute(
                select(Retailer.slug).where(
                    Retailer.tier == tier,
                    Retailer.is_enabled == True,
                )
            )
            return [row[0] for row in result.all()]

    slugs = _run_async(_get_slugs())
    registered = get_all_scrapers()

    for slug in slugs:
        if slug in registered:
            scrape_retailer.delay(slug)
        else:
            logger.debug("No scraper registered for %s, skipping", slug)


@celery_app.task(name="app.tasks.scrape_tasks.scrape_all_enabled")
def scrape_all_enabled():
    """Scrape all enabled retailers across all tiers."""
    for tier in [1, 2, 3]:
        scrape_tier.delay(tier)


@celery_app.task(name="app.tasks.scrape_tasks.trigger_initial_scan")
def trigger_initial_scan():
    """First-run scan: all Tier 1 in parallel immediately, then Tier 2+3 staggered."""
    logger.info("Triggering initial scan — Tier 1 first")
    scrape_tier(1)  # Synchronous — run Tier 1 immediately

    # Queue Tier 2 and 3 with delays
    scrape_tier.apply_async(args=(2,), countdown=120)  # 2 min delay
    scrape_tier.apply_async(args=(3,), countdown=300)  # 5 min delay


@celery_app.task(name="app.tasks.scrape_tasks.test_api_key_task")
def test_api_key_task(key_id: int):
    """Test an API key and update its status."""
    logger.info("Testing API key %d", key_id)

    async def _test():
        async with async_session() as db:
            key = await db.get(ApiKey, key_id)
            if not key:
                return

            plain_key = decrypt_api_key(key.encrypted_key)
            if not plain_key:
                key.is_valid = False
                key.test_status = "decryption_failed"
                await db.commit()
                return

            # TODO: implement actual API testing per service
            # For now, mark as valid if key is non-empty
            key.is_valid = True
            key.test_status = "valid"
            key.last_tested_at = datetime.now(timezone.utc)
            await db.commit()

    _run_async(_test())
