"""Slickdeals RSS feed scraper — instant 20+ deals without any API key."""

import hashlib
import re
from decimal import Decimal
from typing import Optional

from app.scrapers.rss_base import RssScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("slickdeals")
class SlickdealsScraper(RssScraper):
    retailer_slug = "slickdeals"
    feed_url = "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"
    rate_limit_seconds = 1.0

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        entries = await self.fetch_feed()

        self.logger.info("Fetched %d Slickdeals entries", len(entries))

        for entry in entries:
            try:
                product = self._parse_entry(entry)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug("Error parsing Slickdeals entry: %s", e)

        return products

    def _parse_entry(self, entry: dict) -> Optional[ScrapedProduct]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        description = entry.get("summary", "") or entry.get("description", "")

        if not title or not link:
            return None

        # Generate a stable ID from the URL
        external_id = hashlib.md5(link.encode()).hexdigest()[:16]

        # Extract prices from title and description
        deal_price, original_price = self.parse_prices_from_text(f"{title} {description}")

        if not deal_price:
            deal_price = self.parse_price(title)

        if not deal_price or deal_price <= 0:
            # Some entries are just "free" deals
            if "free" in title.lower():
                deal_price = Decimal("0.00")
                original_price = Decimal("10.00")
            else:
                return None

        # Try to extract the actual retailer/store from title
        # e.g. "Samsung TV $299 at Best Buy"
        store = self._extract_store(title)

        # Extract image from description HTML
        image_url = self._extract_image(description)

        # Extract coupon code if present
        coupon_code = self._extract_coupon(f"{title} {description}")

        return ScrapedProduct(
            external_id=external_id,
            name=title[:500],
            url=link,
            image_url=image_url,
            current_price=deal_price,
            original_price=original_price,
            category=store,  # Use store as category for context
            in_stock=True,
            coupon_code=coupon_code,
        )

    def _extract_store(self, title: str) -> Optional[str]:
        stores = [
            "Amazon", "Best Buy", "Walmart", "Target", "Costco", "Newegg",
            "B&H", "Home Depot", "Lowe's", "Staples", "Dell", "Lenovo",
            "HP", "Microsoft", "Apple", "GameStop", "Adorama", "Woot",
        ]
        title_lower = title.lower()
        for store in stores:
            if store.lower() in title_lower:
                return store
        return None

    def _extract_image(self, html: str) -> Optional[str]:
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    def _extract_coupon(self, text: str) -> Optional[str]:
        # Look for patterns like "code: SAVE20" or "coupon: DEAL10"
        patterns = [
            r'code[:\s]+([A-Z0-9]+)',
            r'coupon[:\s]+([A-Z0-9]+)',
            r'promo[:\s]+([A-Z0-9]+)',
            r'use code ([A-Z0-9]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
