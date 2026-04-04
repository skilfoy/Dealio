"""Lenovo scraper — deals page."""

import re
from decimal import Decimal
from typing import Optional

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("lenovo")
class LenovoScraper(PlaywrightScraper):
    retailer_slug = "lenovo"
    rate_limit_seconds = 3.0

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            url = "https://www.lenovo.com/us/en/d/deals/laptops/"
            if not await self.safe_navigate(page, url):
                return products

            await page.wait_for_timeout(3000)
            items = await page.query_selector_all(".product-card, [data-testid='product-card'], .product_item")

            self.logger.info("Found %d Lenovo items", len(items))

            for item in items[:30]:
                try:
                    name_el = await item.query_selector("h3 a, .product-card-title a, .product_title a")
                    if not name_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    href = await name_el.get_attribute("href") or ""

                    match = re.search(r'/([A-Za-z0-9]+)$', href)
                    external_id = match.group(1) if match else name[:20]

                    price_el = await item.query_selector(".final-price, .sale-price, .product-price")
                    if not price_el:
                        continue
                    price_text = await price_el.inner_text()
                    price_match = re.search(r'[\$]?([\d,]+\.?\d*)', price_text.replace(",", ""))
                    if not price_match:
                        continue
                    current_price = Decimal(price_match.group(1))

                    was_el = await item.query_selector(".strike-price, .original-price, .was-price")
                    original_price = None
                    if was_el:
                        was_text = await was_el.inner_text()
                        was_match = re.search(r'[\$]?([\d,]+\.?\d*)', was_text.replace(",", ""))
                        if was_match:
                            original_price = Decimal(was_match.group(1))

                    img_el = await item.query_selector("img")
                    image_url = await img_el.get_attribute("src") if img_el else None

                    products.append(ScrapedProduct(
                        external_id=external_id,
                        name=name[:500],
                        url=href if href.startswith("http") else f"https://www.lenovo.com{href}",
                        image_url=image_url,
                        current_price=current_price,
                        original_price=original_price if original_price and original_price > current_price else None,
                        category="Computers",
                        in_stock=True,
                    ))
                except Exception as e:
                    self.logger.debug("Error parsing Lenovo item: %s", e)

        finally:
            await browser.close()
            await pw.stop()

        return products
