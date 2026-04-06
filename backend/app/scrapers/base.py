"""Base scraper with run() orchestration.

Flow: scrape → upsert products → detect price changes on EVERY update →
      record history → calculate deal score → publish to Redis IMMEDIATELY
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deal_scorer import calculate_deal_score
from app.core.price_error_detector import detect_price_error, classify_deal_type
from app.core.redis import publish_deal_sync
from app.models.deal import Deal
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.retailer import Retailer
from app.models.scrape_job import ScrapeJob


class ScrapedProduct(BaseModel):
    external_id: str
    name: str
    url: str
    image_url: Optional[str] = None
    current_price: Decimal
    original_price: Optional[Decimal] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    in_stock: bool = True
    coupon_code: Optional[str] = None
    coupon_discount: Optional[Decimal] = None
    model_number: Optional[str] = None
    upc: Optional[str] = None
    is_clearance: bool = False


class ScrapeResult(BaseModel):
    items_found: int = 0
    deals_found: int = 0
    errors: list[str] = []


class BaseScraper(ABC):
    retailer_slug: str = ""
    scraper_type: str = "api"  # api, playwright, rss

    def __init__(self, db: AsyncSession, api_key: Optional[str] = None):
        self.db = db
        self.api_key = api_key
        self.logger = logging.getLogger(f"scraper.{self.retailer_slug}")
        self._retailer: Optional[Retailer] = None
        self._scrape_job: Optional[ScrapeJob] = None

    async def get_retailer(self) -> Retailer:
        if self._retailer is None:
            result = await self.db.execute(select(Retailer).where(Retailer.slug == self.retailer_slug))
            self._retailer = result.scalars().first()
        return self._retailer

    @abstractmethod
    async def scrape(self) -> list[ScrapedProduct]:
        """Implement in subclass — fetch products from retailer."""
        ...

    async def run(self) -> ScrapeResult:
        """Main orchestration — scrape, upsert, detect deals, publish."""
        retailer = await self.get_retailer()
        if not retailer:
            self.logger.error("Retailer %s not found in database", self.retailer_slug)
            return ScrapeResult(errors=[f"Retailer {self.retailer_slug} not found"])

        # Create scrape job
        self._scrape_job = ScrapeJob(retailer_id=retailer.id, status="running", started_at=datetime.utcnow())
        self.db.add(self._scrape_job)
        await self.db.commit()

        result = ScrapeResult()

        try:
            products = await self.scrape()
            result.items_found = len(products)
            self.logger.info("Scraped %d products from %s", len(products), self.retailer_slug)

            for scraped in products:
                try:
                    deal = await self._process_product(scraped, retailer)
                    if deal:
                        result.deals_found += 1
                except Exception as e:
                    self.logger.warning("Error processing product %s: %s", scraped.external_id, e)
                    result.errors.append(str(e))

            # Update retailer stats
            retailer.last_scraped_at = datetime.utcnow()
            retailer.total_deals_found += result.deals_found

            self._scrape_job.status = "completed"
            self._scrape_job.items_found = result.items_found
            self._scrape_job.deals_found = result.deals_found
            self._scrape_job.completed_at = datetime.utcnow()
            await self.db.commit()

        except Exception as e:
            self.logger.error("Scraper %s failed: %s", self.retailer_slug, e)
            self._scrape_job.status = "failed"
            self._scrape_job.error_message = str(e)[:1000]
            self._scrape_job.completed_at = datetime.utcnow()
            await self.db.commit()
            result.errors.append(str(e))

        return result

    async def _process_product(self, scraped: ScrapedProduct, retailer: Retailer) -> Optional[Deal]:
        """Upsert product, detect price change, create deal if warranted."""
        # Find or create product
        result = await self.db.execute(
            select(Product).where(Product.retailer_id == retailer.id, Product.external_id == scraped.external_id)
        )
        product = result.scalars().first()
        old_price = product.current_price if product else None

        if product:
            product.name = scraped.name
            product.url = scraped.url
            product.image_url = scraped.image_url or product.image_url
            product.category = scraped.category or product.category
            product.brand = scraped.brand or product.brand
            product.original_price = scraped.original_price or product.original_price
            product.in_stock = scraped.in_stock
            product.coupon_code = scraped.coupon_code
            product.coupon_discount = scraped.coupon_discount
            product.current_price = scraped.current_price
            product.last_checked_at = datetime.utcnow()
            # Calculate true final price
            if scraped.coupon_discount and scraped.coupon_discount > 0:
                product.true_final_price = scraped.current_price - scraped.coupon_discount
            else:
                product.true_final_price = scraped.current_price
        else:
            true_final = scraped.current_price
            if scraped.coupon_discount and scraped.coupon_discount > 0:
                true_final = scraped.current_price - scraped.coupon_discount
            product = Product(
                retailer_id=retailer.id,
                external_id=scraped.external_id,
                name=scraped.name,
                url=scraped.url,
                image_url=scraped.image_url,
                category=scraped.category,
                brand=scraped.brand,
                model_number=scraped.model_number,
                upc=scraped.upc,
                current_price=scraped.current_price,
                original_price=scraped.original_price,
                coupon_code=scraped.coupon_code,
                coupon_discount=scraped.coupon_discount,
                true_final_price=true_final,
                in_stock=scraped.in_stock,
                last_checked_at=datetime.utcnow(),
            )
            self.db.add(product)
            await self.db.flush()

        # Record price history
        coupon_adj = None
        if scraped.coupon_discount and scraped.coupon_discount > 0:
            coupon_adj = scraped.current_price - scraped.coupon_discount
        history = PriceHistory(
            product_id=product.id,
            price=scraped.current_price,
            original_price=scraped.original_price,
            coupon_adjusted_price=coupon_adj,
            in_stock=scraped.in_stock,
        )
        self.db.add(history)

        # Detect deals — runs on EVERY price update
        deal = await self._detect_and_create_deal(product, scraped, retailer, old_price)
        await self.db.flush()
        return deal

    async def _detect_and_create_deal(
        self,
        product: Product,
        scraped: ScrapedProduct,
        retailer: Retailer,
        old_price: Optional[Decimal],
    ) -> Optional[Deal]:
        """Check if this price update constitutes a deal."""
        effective_price = product.true_final_price or scraped.current_price
        reference_price = scraped.original_price or old_price

        if not reference_price or reference_price <= 0:
            return None

        discount_pct = float((reference_price - effective_price) / reference_price * 100)

        if discount_pct < 40:  # Below threshold
            return None

        # Get historical price data
        hist_count_result = await self.db.execute(
            select(func.count()).where(PriceHistory.product_id == product.id)
        )
        history_count = hist_count_result.scalar() or 0

        avg_result = await self.db.execute(
            select(func.avg(PriceHistory.price)).where(PriceHistory.product_id == product.id)
        )
        avg_price = avg_result.scalar()

        min_result = await self.db.execute(
            select(func.min(PriceHistory.price)).where(PriceHistory.product_id == product.id)
        )
        historical_low = min_result.scalar()

        is_historical_low = historical_low is not None and effective_price <= historical_low

        # Price error detection
        is_delivery = retailer.slug in ("doordash",)
        is_error, error_reason = detect_price_error(
            new_price=effective_price,
            previous_price=old_price,
            original_price=scraped.original_price,
            avg_historical_price=Decimal(str(avg_price)) if avg_price else None,
            is_delivery_app=is_delivery,
        )

        deal_type = classify_deal_type(
            discount_percent=discount_pct,
            is_price_error=is_error,
            is_delivery_app=is_delivery,
            has_coupon=bool(scraped.coupon_code),
            is_clearance=scraped.is_clearance,
        )

        now = datetime.utcnow()
        deal_score = calculate_deal_score(
            discount_percent=discount_pct,
            price_history_count=history_count,
            in_stock=scraped.in_stock,
            retailer_tier=retailer.tier,
            deal_type=deal_type,
            found_at=now,
            is_historical_low=is_historical_low,
        )

        # Check if deal already exists for this product
        existing = await self.db.execute(
            select(Deal).where(Deal.product_id == product.id, Deal.is_active == True)
        )
        existing_deal = existing.scalars().first()

        if existing_deal:
            existing_deal.deal_price = effective_price
            existing_deal.regular_price = reference_price
            existing_deal.discount_percent = Decimal(str(round(discount_pct, 2)))
            existing_deal.deal_score = deal_score
            existing_deal.deal_type = deal_type
            existing_deal.last_seen_at = now
            existing_deal.is_historical_low = is_historical_low
            existing_deal.coupon_code = scraped.coupon_code
            deal = existing_deal
        else:
            deal = Deal(
                product_id=product.id,
                retailer_id=retailer.id,
                deal_type=deal_type,
                deal_price=effective_price,
                regular_price=reference_price,
                discount_percent=Decimal(str(round(discount_pct, 2))),
                deal_score=deal_score,
                coupon_code=scraped.coupon_code,
                title=product.name,
                source_url=product.url,
                image_url=product.image_url,
                is_active=True,
                is_historical_low=is_historical_low,
                found_at=now,
                last_seen_at=now,
            )
            self.db.add(deal)
            await self.db.flush()

        # Publish to Redis IMMEDIATELY
        self._publish_deal(deal, product, retailer)
        return deal

    def _publish_deal(self, deal: Deal, product: Product, retailer: Retailer) -> None:
        """Push deal to SSE stream the instant it's found."""
        try:
            publish_deal_sync({
                "id": deal.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_url": product.url,
                "product_image": product.image_url,
                "retailer_name": retailer.name,
                "retailer_slug": retailer.slug,
                "deal_type": deal.deal_type,
                "deal_price": str(deal.deal_price),
                "regular_price": str(deal.regular_price),
                "discount_percent": str(deal.discount_percent),
                "deal_score": deal.deal_score,
                "coupon_code": deal.coupon_code,
                "is_historical_low": deal.is_historical_low,
                "found_at": deal.found_at.isoformat() if deal.found_at else None,
            })
        except Exception as e:
            self.logger.warning("Failed to publish deal to Redis: %s", e)
