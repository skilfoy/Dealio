"""Keepa API scraper — crown jewel when API key is present.

Provides full Amazon price history, deal alerts, and historical low detection.
Requires a Keepa API key ($19+/month).
"""

from decimal import Decimal
from typing import Optional

from app.scrapers.api_base import ApiScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("keepa")
class KeepaScraper(ApiScraper):
    retailer_slug = "keepa"
    base_api_url = "https://api.keepa.com"
    rate_limit_seconds = 2.0

    async def scrape(self) -> list[ScrapedProduct]:
        if not self.api_key:
            self.logger.info("Keepa API key not configured — skipping")
            return []

        products = []

        # Get top deals from Keepa
        try:
            deals = await self._fetch_deals()
            products.extend(deals)
        except Exception as e:
            self.logger.warning("Error fetching Keepa deals: %s", e)

        return products

    async def _fetch_deals(self) -> list[ScrapedProduct]:
        products = []

        # Keepa deals endpoint
        url = f"{self.base_api_url}/deal"
        params = {
            "key": self.api_key,
            "domain": "1",  # Amazon.com
            "page": "0",
            "priceTypes": "0",  # Amazon price
            "percentRange": "50,100",  # 50-100% off
            "isRangeEnabled": "true",
            "hasReviews": "true",
            "isBackInStock": "false",
            "isOutOfStock": "false",
        }

        data = await self.fetch_json(url, params=params)
        if not data or "deals" not in data.get("deals", {}):
            data_deals = data.get("deals") if data else None
            if not data_deals:
                return products
            deal_list = data_deals if isinstance(data_deals, list) else data_deals.get("dr", [])
        else:
            deal_list = data["deals"].get("dr", [])

        for deal in deal_list[:50]:
            try:
                asin = deal.get("asin", "")
                if not asin:
                    continue

                title = deal.get("title", "Amazon Product")
                current = deal.get("current", [0])[0] if deal.get("current") else 0
                avg30 = deal.get("avg", [0, 0, 0])[0] if deal.get("avg") else 0

                # Keepa prices are in cents
                current_price = Decimal(str(current / 100)) if current > 0 else Decimal("0")
                avg_price = Decimal(str(avg30 / 100)) if avg30 > 0 else None

                if current_price <= 0:
                    continue

                image_url = None
                if deal.get("images"):
                    image_url = f"https://images-na.ssl-images-amazon.com/images/I/{deal['images'][0]}"

                products.append(ScrapedProduct(
                    external_id=asin,
                    name=title[:500],
                    url=f"https://www.amazon.com/dp/{asin}",
                    image_url=image_url,
                    current_price=current_price,
                    original_price=avg_price if avg_price and avg_price > current_price else None,
                    category=deal.get("categoryTree", [{}])[0].get("name") if deal.get("categoryTree") else None,
                    brand=deal.get("brand"),
                    in_stock=True,
                ))
            except (KeyError, ValueError, TypeError, IndexError) as e:
                self.logger.debug("Error parsing Keepa deal: %s", e)

        return products
