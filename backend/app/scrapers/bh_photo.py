"""B&H Photo scraper — Deal Zone page."""

import re
from decimal import Decimal
from typing import Optional

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("bh-photo")
class BHPhotoScraper(PlaywrightScraper):
    retailer_slug = "bh-photo"
    rate_limit_seconds = 3.0

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            url = "https://www.bhphotovideo.com/c/browse/Deal-Zone/ci/18985/N/4294966104"
            if not await self.safe_navigate(page, url):
                return products

            await page.wait_for_timeout(3000)
            items = await page.query_selector_all("[data-selenium='miniProductPage'], .sku-item")

            self.logger.info("Found %d B&H items", len(items))

            for item in items[:40]:
                try:
                    name_el = await item.query_selector("[data-selenium='miniProductPageProductName'], .sku-title a")
                    if not name_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    href = await name_el.get_attribute("href") or ""

                    match = re.search(r'/(\d+)-REG', href)
                    external_id = match.group(1) if match else name[:20].replace(" ", "")

                    price_el = await item.query_selector("[data-selenium='pricingPrice'], .sku-price")
                    if not price_el:
                        continue
                    price_text = await price_el.inner_text()
                    price_match = re.search(r'[\$]?([\d,]+\.?\d*)', price_text.replace(",", ""))
                    if not price_match:
                        continue
                    current_price = Decimal(price_match.group(1))

                    was_el = await item.query_selector("[data-selenium='strikeThroughPrice'], .sku-original-price")
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
                        url=href if href.startswith("http") else f"https://www.bhphotovideo.com{href}",
                        image_url=image_url,
                        current_price=current_price,
                        original_price=original_price if original_price and original_price > current_price else None,
                        category="Electronics",
                        in_stock=True,
                    ))
                except Exception as e:
                    self.logger.debug("Error parsing B&H item: %s", e)

        finally:
            await browser.close()
            await pw.stop()

        return products
