"""Base class for RSS/Atom feed scrapers."""

import re
from decimal import Decimal
from typing import Optional

import feedparser

from app.scrapers.api_base import ApiScraper
from app.scrapers.base import ScrapedProduct


class RssScraper(ApiScraper):
    scraper_type = "rss"
    feed_url: str = ""

    async def fetch_feed(self) -> list[dict]:
        text = await self.fetch_text(self.feed_url)
        if not text:
            return []
        feed = feedparser.parse(text)
        return feed.entries

    def parse_price(self, text: str) -> Optional[Decimal]:
        """Extract price from text like '$29.99' or 'was $59.99'."""
        if not text:
            return None
        matches = re.findall(r'\$[\d,]+\.?\d*', text)
        if matches:
            price_str = matches[0].replace('$', '').replace(',', '')
            try:
                return Decimal(price_str)
            except Exception:
                pass
        return None

    def parse_prices_from_text(self, text: str) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """Extract deal price and original price from deal description text."""
        prices = re.findall(r'\$[\d,]+\.?\d*', text or "")
        if len(prices) >= 2:
            vals = []
            for p in prices[:3]:
                try:
                    vals.append(Decimal(p.replace('$', '').replace(',', '')))
                except Exception:
                    pass
            if len(vals) >= 2:
                return min(vals), max(vals)
        elif len(prices) == 1:
            try:
                return Decimal(prices[0].replace('$', '').replace(',', '')), None
            except Exception:
                pass
        return None, None
