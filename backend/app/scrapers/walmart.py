"""Walmart scraper using public search/browse APIs.

Searches for clearance and rollback items.
"""

from decimal import Decimal

from app.scrapers.api_base import ApiScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("walmart")
class WalmartScraper(ApiScraper):
    retailer_slug = "walmart"
    base_api_url = "https://www.walmart.com"
    rate_limit_seconds = 2.0

    DEAL_SEARCHES = [
        "clearance electronics",
        "rollback deals",
        "reduced price tv",
        "clearance laptops",
        "flash deals",
        "clearance home",
    ]

    async def scrape(self) -> list[ScrapedProduct]:
        products = []

        for query in self.DEAL_SEARCHES:
            try:
                items = await self._search(query)
                products.extend(items)
            except Exception as e:
                self.logger.warning("Walmart search error for '%s': %s", query, e)

        seen = set()
        unique = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique.append(p)
        return unique

    async def _search(self, query: str) -> list[ScrapedProduct]:
        products = []

        url = f"{self.base_api_url}/search/api/preso"
        params = {
            "q": query,
            "sort": "best_match",
            "page": "1",
            "prg": "desktop",
            "ps": "40",
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        }

        data = await self.fetch_json(url, params=params, headers=headers)
        if not data:
            # Fallback: try the tempo API
            data = await self._try_tempo_api(query)
            if not data:
                return products

        items = data.get("items", [])
        if not items:
            items = data.get("searchResult", {}).get("items", [])

        for item in items:
            try:
                price_info = item.get("priceInfo", {}) or item.get("price", {})

                current = price_info.get("currentPrice", {}).get("price") or price_info.get("price", 0)
                was_price = price_info.get("wasPrice", {}).get("price") or price_info.get("wasPrice", 0)

                current_price = Decimal(str(current))
                original_price = Decimal(str(was_price)) if was_price else None

                if current_price <= 0:
                    continue

                item_id = str(item.get("id", "") or item.get("usItemId", ""))
                if not item_id:
                    continue

                is_rollback = item.get("flag", "") == "ROLLBACK" or "rollback" in str(item.get("badges", "")).lower()

                products.append(ScrapedProduct(
                    external_id=item_id,
                    name=item.get("name", "") or item.get("title", "Unknown"),
                    url=f"https://www.walmart.com/ip/{item_id}",
                    image_url=item.get("image", "") or item.get("imageUrl", ""),
                    current_price=current_price,
                    original_price=original_price if original_price and original_price > current_price else None,
                    category=item.get("category", {}).get("path", "") if isinstance(item.get("category"), dict) else None,
                    brand=item.get("brand"),
                    in_stock=item.get("availabilityStatus", "") != "OUT_OF_STOCK",
                    is_clearance=is_rollback or item.get("flag", "") == "CLEARANCE",
                ))
            except (KeyError, ValueError, TypeError) as e:
                self.logger.debug("Skipping Walmart item: %s", e)

        return products

    async def _try_tempo_api(self, query: str) -> dict | None:
        url = "https://www.walmart.com/orchestra/home/graphql"
        # Fallback search attempt
        return None
