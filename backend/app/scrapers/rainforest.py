"""Rainforest API scraper — Amazon product data enrichment.

Requires API key. Provides real-time Amazon product data.
"""

from decimal import Decimal

from app.scrapers.api_base import ApiScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("rainforest")
class RainforestScraper(ApiScraper):
    retailer_slug = "rainforest"
    base_api_url = "https://api.rainforestapi.com"
    rate_limit_seconds = 2.0

    async def scrape(self) -> list[ScrapedProduct]:
        if not self.api_key:
            self.logger.info("Rainforest API key not configured — skipping")
            return []

        products = []

        # Search for deals across categories
        categories = [
            "electronics deals",
            "computer deals",
            "home deals 50 off",
        ]

        for query in categories:
            try:
                items = await self._search(query)
                products.extend(items)
            except Exception as e:
                self.logger.warning("Rainforest search error for '%s': %s", query, e)

        seen = set()
        return [p for p in products if not (p.external_id in seen or seen.add(p.external_id))]

    async def _search(self, query: str) -> list[ScrapedProduct]:
        products = []

        url = f"{self.base_api_url}/request"
        params = {
            "api_key": self.api_key,
            "type": "search",
            "amazon_domain": "amazon.com",
            "search_term": query,
            "sort_by": "price_low_to_high",
        }

        data = await self.fetch_json(url, params=params)
        if not data or "search_results" not in data:
            return products

        for item in data["search_results"][:20]:
            try:
                asin = item.get("asin", "")
                if not asin:
                    continue

                price = item.get("price", {})
                current_price = Decimal(str(price.get("value", 0)))
                if current_price <= 0:
                    continue

                rrp = item.get("rrp", {})
                original_price = Decimal(str(rrp.get("value", 0))) if rrp.get("value") else None

                coupon = item.get("coupon", {})
                coupon_code = None
                coupon_discount = None
                if coupon:
                    if coupon.get("badge_text"):
                        coupon_code = coupon["badge_text"]
                    if coupon.get("amount"):
                        coupon_discount = Decimal(str(coupon["amount"]))

                products.append(ScrapedProduct(
                    external_id=asin,
                    name=item.get("title", "")[:500],
                    url=item.get("link", f"https://www.amazon.com/dp/{asin}"),
                    image_url=item.get("image"),
                    current_price=current_price,
                    original_price=original_price if original_price and original_price > current_price else None,
                    category=item.get("categories", [{}])[0].get("name") if item.get("categories") else None,
                    brand=item.get("brand"),
                    in_stock=item.get("availability", {}).get("raw", "") != "Currently unavailable",
                    coupon_code=coupon_code,
                    coupon_discount=coupon_discount,
                ))
            except (KeyError, ValueError, TypeError) as e:
                self.logger.debug("Error parsing Rainforest item: %s", e)

        return products
