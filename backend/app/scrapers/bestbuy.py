"""Best Buy scraper using their open API.

Works without an API key for basic access (1 req/sec).
With API key: higher rate limits and full catalog access.
Endpoint: https://api.bestbuy.com/v1/products
"""

from decimal import Decimal
from typing import Optional

from app.scrapers.api_base import ApiScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("best-buy")
class BestBuyScraper(ApiScraper):
    retailer_slug = "best-buy"
    base_api_url = "https://api.bestbuy.com/v1"
    rate_limit_seconds = 1.0

    async def scrape(self) -> list[ScrapedProduct]:
        products = []

        # Search for products on sale with significant discounts
        queries = [
            "(onSale=true&percentSavings>50)",
            "(onSale=true&percentSavings>40&categoryPath.id=pcmcat209400050001)",  # TVs
            "(onSale=true&percentSavings>40&categoryPath.id=abcat0502000)",  # Laptops
            "(onSale=true&percentSavings>40&categoryPath.id=pcmcat241600050001)",  # Headphones
            "(onSale=true&percentSavings>40&categoryPath.id=abcat0904000)",  # Appliances
        ]

        api_key = self.api_key or ""
        if not api_key:
            # Use basic access — limited but works
            self.logger.info("No Best Buy API key — using basic access")

        for query in queries:
            try:
                page_items = await self._fetch_products(query, api_key)
                products.extend(page_items)
            except Exception as e:
                self.logger.warning("Error fetching Best Buy query %s: %s", query, e)

        # Deduplicate by SKU
        seen = set()
        unique = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique.append(p)

        return unique

    async def _fetch_products(self, query: str, api_key: str) -> list[ScrapedProduct]:
        products = []
        params = {
            "format": "json",
            "show": "sku,name,salePrice,regularPrice,percentSavings,url,image,categoryPath,manufacturer,modelNumber,upc,onSale,inStoreAvailability,onlineAvailabilityText",
            "pageSize": "100",
            "page": "1",
        }
        if api_key:
            params["apiKey"] = api_key

        url = f"{self.base_api_url}/products{query}"
        data = await self.fetch_json(url, params=params)

        if not data or "products" not in data:
            return products

        for item in data.get("products", []):
            try:
                sale_price = Decimal(str(item.get("salePrice", 0)))
                regular_price = Decimal(str(item.get("regularPrice", 0)))

                if sale_price <= 0:
                    continue

                category = None
                cat_path = item.get("categoryPath", [])
                if cat_path and len(cat_path) > 1:
                    category = cat_path[1].get("name", "")

                products.append(ScrapedProduct(
                    external_id=str(item["sku"]),
                    name=item.get("name", "Unknown"),
                    url=item.get("url", f"https://www.bestbuy.com/site/{item['sku']}.p"),
                    image_url=item.get("image"),
                    current_price=sale_price,
                    original_price=regular_price if regular_price > sale_price else None,
                    category=category,
                    brand=item.get("manufacturer"),
                    model_number=item.get("modelNumber"),
                    upc=item.get("upc"),
                    in_stock="Available" in str(item.get("onlineAvailabilityText", "")),
                ))
            except (KeyError, ValueError, TypeError) as e:
                self.logger.debug("Skipping Best Buy item: %s", e)

        return products
