"""Woot.com daily deals scraper — works without API key.

Woot (owned by Amazon) publishes daily deals via their API.
"""

from decimal import Decimal
from typing import Optional

from app.scrapers.api_base import ApiScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("woot")
class WootScraper(ApiScraper):
    retailer_slug = "woot"
    base_api_url = "https://api.woot.com/2"
    rate_limit_seconds = 2.0

    FEED_TYPES = [
        "www.woot.com",
        "electronics.woot.com",
        "computers.woot.com",
        "home.woot.com",
        "tools.woot.com",
    ]

    async def scrape(self) -> list[ScrapedProduct]:
        products = []

        # Try the current offers endpoint
        for feed in self.FEED_TYPES:
            try:
                items = await self._fetch_feed(feed)
                products.extend(items)
            except Exception as e:
                self.logger.warning("Error fetching Woot feed %s: %s", feed, e)

        seen = set()
        unique = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique.append(p)
        return unique

    async def _fetch_feed(self, feed_name: str) -> list[ScrapedProduct]:
        products = []

        url = f"{self.base_api_url}/events.json"
        params = {"site": feed_name}
        headers = {"Accept": "application/json"}

        data = await self.fetch_json(url, params=params, headers=headers)

        if not data:
            # Fallback: try alternate endpoint
            alt_url = f"https://api.woot.com/1/sales/current.json/{feed_name}"
            data = await self.fetch_json(alt_url)
            if data and isinstance(data, dict):
                data = [data]

        if not data:
            return products

        items_list = data if isinstance(data, list) else [data]

        for event in items_list:
            try:
                offers = event.get("Offers", [])
                if not offers:
                    offers = [event] if "Title" in event else []

                for offer in offers:
                    items = offer.get("Items", [{}])
                    title = offer.get("Title", "") or event.get("Title", "")

                    for item in items:
                        sale_price = item.get("SalePrice") or offer.get("MinPrice") or 0
                        list_price = item.get("ListPrice") or offer.get("ListPrice") or 0

                        if not sale_price:
                            continue

                        current_price = Decimal(str(sale_price))
                        original_price = Decimal(str(list_price)) if list_price and list_price > sale_price else None

                        if current_price <= 0:
                            continue

                        item_id = str(item.get("Id", "") or offer.get("Id", "") or event.get("EventId", ""))
                        if not item_id:
                            continue

                        # Extract image
                        photos = offer.get("Photos", []) or event.get("Photos", [])
                        image_url = photos[0].get("Url", "") if photos else None

                        url = offer.get("Url", "") or event.get("Url", "") or f"https://www.woot.com"

                        products.append(ScrapedProduct(
                            external_id=item_id,
                            name=(item.get("Title", "") or title)[:500],
                            url=url,
                            image_url=image_url,
                            current_price=current_price,
                            original_price=original_price,
                            category=feed_name.split(".")[0] if "." in feed_name else "daily",
                            brand=item.get("Brand", {}).get("Name") if isinstance(item.get("Brand"), dict) else None,
                            in_stock=item.get("QuantityAvailable", 1) > 0 if "QuantityAvailable" in item else True,
                        ))
            except (KeyError, ValueError, TypeError) as e:
                self.logger.debug("Error parsing Woot event: %s", e)

        return products
