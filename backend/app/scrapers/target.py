"""Target scraper using the RedSky API (public, no auth needed).

Endpoint: https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2
"""

from decimal import Decimal

from app.scrapers.api_base import ApiScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("target")
class TargetScraper(ApiScraper):
    retailer_slug = "target"
    base_api_url = "https://redsky.target.com"
    rate_limit_seconds = 2.0

    CLEARANCE_CATEGORIES = [
        "5xtdj",  # Clearance - Electronics
        "5xsxu",  # Clearance - Home
        "5xsy1",  # Clearance - Toys
        "5xsy6",  # Clearance - Kitchen
        "4yi4h",  # Top Deals
    ]

    async def scrape(self) -> list[ScrapedProduct]:
        products = []

        for category_id in self.CLEARANCE_CATEGORIES:
            try:
                items = await self._fetch_category(category_id)
                products.extend(items)
            except Exception as e:
                self.logger.warning("Error fetching Target category %s: %s", category_id, e)

        # Also search for deals via keyword
        for keyword in ["clearance electronics", "price cut", "sale 50 off"]:
            try:
                items = await self._search(keyword)
                products.extend(items)
            except Exception as e:
                self.logger.warning("Error searching Target for '%s': %s", keyword, e)

        # Deduplicate
        seen = set()
        unique = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique.append(p)
        return unique

    async def _fetch_category(self, category_id: str) -> list[ScrapedProduct]:
        url = f"{self.base_api_url}/redsky_aggregations/v1/web/plp_search_v2"
        params = {
            "key": "9f36aeafbe60771e321a7cc95a78140772ab3e96",
            "category": category_id,
            "channel": "WEB",
            "count": "24",
            "default_purchasability_filter": "true",
            "offset": "0",
            "page": f"/c/{category_id}",
            "pricing_store_id": "3991",
            "store_ids": "3991",
            "visitor_id": "DealRadar",
        }
        return await self._parse_response(url, params)

    async def _search(self, keyword: str) -> list[ScrapedProduct]:
        url = f"{self.base_api_url}/redsky_aggregations/v1/web/plp_search_v2"
        params = {
            "key": "9f36aeafbe60771e321a7cc95a78140772ab3e96",
            "keyword": keyword,
            "channel": "WEB",
            "count": "24",
            "default_purchasability_filter": "true",
            "offset": "0",
            "pricing_store_id": "3991",
            "visitor_id": "DealRadar",
        }
        return await self._parse_response(url, params)

    async def _parse_response(self, url: str, params: dict) -> list[ScrapedProduct]:
        products = []
        data = await self.fetch_json(url, params=params)

        if not data:
            return products

        search_data = data.get("data", {}).get("search", {})
        items = search_data.get("products", [])

        for item in items:
            try:
                tcin = item.get("tcin", "")
                item_data = item.get("item", {})
                price_data = item.get("price", {})

                current = price_data.get("current_retail") or price_data.get("formatted_current_price", "0")
                if isinstance(current, str):
                    current = current.replace("$", "").replace(",", "")
                current_price = Decimal(str(current))

                reg = price_data.get("reg_retail", 0)
                regular_price = Decimal(str(reg)) if reg else None

                if current_price <= 0:
                    continue

                enrichment = item_data.get("enrichment", {})
                images = enrichment.get("images", {})
                primary_image = images.get("primary_image_url", "")

                products.append(ScrapedProduct(
                    external_id=str(tcin),
                    name=item_data.get("product_description", {}).get("title", "Unknown"),
                    url=f"https://www.target.com/p/-/A-{tcin}",
                    image_url=primary_image,
                    current_price=current_price,
                    original_price=regular_price if regular_price and regular_price > current_price else None,
                    category=item_data.get("product_classification", {}).get("product_type_name"),
                    brand=item_data.get("product_description", {}).get("upstream_brand", {}).get("brand"),
                    in_stock=price_data.get("availability_status", "") == "IN_STOCK",
                    is_clearance=price_data.get("is_current_price_range", False) or "clearance" in str(data.get("data", {}).get("search", {}).get("search_response", {}).get("typed_metadata", {}).get("category", "")).lower(),
                ))
            except (KeyError, ValueError, TypeError) as e:
                self.logger.debug("Skipping Target item: %s", e)

        return products
