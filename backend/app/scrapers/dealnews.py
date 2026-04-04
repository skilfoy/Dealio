"""DealNews RSS feed scraper — instant 20+ deals without any API key."""

import hashlib
import re
from decimal import Decimal
from typing import Optional

from app.scrapers.rss_base import RssScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("dealnews")
class DealNewsScraper(RssScraper):
    retailer_slug = "dealnews"
    feed_url = "https://www.dealnews.com/rss/frontpage.xml"
    rate_limit_seconds = 1.0

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        entries = await self.fetch_feed()

        self.logger.info("Fetched %d DealNews entries", len(entries))

        for entry in entries:
            try:
                product = self._parse_entry(entry)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug("Error parsing DealNews entry: %s", e)

        return products

    def _parse_entry(self, entry: dict) -> Optional[ScrapedProduct]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        description = entry.get("summary", "") or entry.get("description", "")

        if not title or not link:
            return None

        external_id = hashlib.md5(link.encode()).hexdigest()[:16]

        deal_price, original_price = self.parse_prices_from_text(f"{title} {description}")
        if not deal_price:
            deal_price = self.parse_price(title)

        if not deal_price or deal_price <= 0:
            if "free" in title.lower():
                deal_price = Decimal("0.00")
                original_price = Decimal("10.00")
            else:
                return None

        image_url = self._extract_image(description)
        coupon_code = self._extract_coupon(f"{title} {description}")

        return ScrapedProduct(
            external_id=external_id,
            name=title[:500],
            url=link,
            image_url=image_url,
            current_price=deal_price,
            original_price=original_price,
            in_stock=True,
            coupon_code=coupon_code,
        )

    def _extract_image(self, html: str) -> Optional[str]:
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        return match.group(1) if match else None

    def _extract_coupon(self, text: str) -> Optional[str]:
        patterns = [
            r'code[:\s]+"?([A-Z0-9]+)"?',
            r'coupon[:\s]+"?([A-Z0-9]+)"?',
            r'promo[:\s]+"?([A-Z0-9]+)"?',
            r'use code "?([A-Z0-9]+)"?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and len(match.group(1)) >= 3:
                return match.group(1)
        return None
