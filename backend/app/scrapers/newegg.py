"""Newegg scraper — Shell Shocker deals and daily deals page."""

import re
from decimal import Decimal
from typing import Optional

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("newegg")
class NeweggScraper(PlaywrightScraper):
    retailer_slug = "newegg"
    rate_limit_seconds = 3.0

    DEAL_URLS = [
        "https://www.newegg.com/todays-deals",
        "https://www.newegg.com/Shell-Shocker/EventSaleStore/ID-5",
    ]

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            for url in self.DEAL_URLS:
                try:
                    if not await self.safe_navigate(page, url):
                        continue
                    await page.wait_for_timeout(2000)

                    items = await page.query_selector_all(".item-cell, .item-container, [class*='product-']")
                    self.logger.info("Found %d Newegg items on %s", len(items), url)

                    for item in items[:40]:
                        try:
                            product = await self._parse_item(item)
                            if product:
                                products.append(product)
                        except Exception as e:
                            self.logger.debug("Error parsing Newegg item: %s", e)
                except Exception as e:
                    self.logger.warning("Error scraping Newegg page %s: %s", url, e)
        finally:
            await browser.close()
            await pw.stop()

        seen = set()
        return [p for p in products if not (p.external_id in seen or seen.add(p.external_id))]

    async def _parse_item(self, item) -> Optional[ScrapedProduct]:
        link = await item.query_selector("a.item-title, a[href*='/p/']")
        if not link:
            return None

        href = await link.get_attribute("href") or ""
        name = (await link.inner_text()).strip()

        # Extract item number from URL
        match = re.search(r'/p/([A-Z0-9]+)', href)
        if not match:
            match = re.search(r'Item=([A-Z0-9]+)', href)
        external_id = match.group(1) if match else href[-20:]

        price_el = await item.query_selector(".price-current, .price-was-price + .price-current")
        if not price_el:
            return None
        price_text = await price_el.inner_text()
        current_price = self._parse_price(price_text)
        if not current_price or current_price <= 0:
            return None

        was_el = await item.query_selector(".price-was-data, .price-was")
        original_price = None
        if was_el:
            was_text = await was_el.inner_text()
            original_price = self._parse_price(was_text)

        img_el = await item.query_selector("img")
        image_url = await img_el.get_attribute("src") if img_el else None

        return ScrapedProduct(
            external_id=external_id,
            name=name[:500],
            url=href if href.startswith("http") else f"https://www.newegg.com{href}",
            image_url=image_url,
            current_price=current_price,
            original_price=original_price if original_price and original_price > current_price else None,
            category="Electronics",
            in_stock=True,
        )

    def _parse_price(self, text: str) -> Optional[Decimal]:
        match = re.search(r'[\$]?([\d,]+\.?\d*)', text.replace(",", ""))
        if match:
            try:
                return Decimal(match.group(1))
            except Exception:
                pass
        return None
