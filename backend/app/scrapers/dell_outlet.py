"""Dell Outlet scraper — refurbished and outlet deals."""

import re
from decimal import Decimal

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("dell-outlet")
class DellOutletScraper(PlaywrightScraper):
    retailer_slug = "dell-outlet"
    rate_limit_seconds = 3.0

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            url = "https://www.dell.com/en-us/shop/dell-refurbished/ar/4010"
            if not await self.safe_navigate(page, url):
                return products

            await page.wait_for_timeout(3000)
            items = await page.query_selector_all(".product-card, .ps-product, [data-testid='product-card']")

            self.logger.info("Found %d Dell Outlet items", len(items))

            for item in items[:30]:
                try:
                    name_el = await item.query_selector("h3 a, .product-title a, [data-testid='product-title'] a")
                    if not name_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    href = await name_el.get_attribute("href") or ""

                    match = re.search(r'/([a-z0-9-]+)$', href)
                    external_id = f"dell-outlet-{match.group(1)}" if match else f"dell-outlet-{name[:20]}"

                    price_el = await item.query_selector(".sale-price, .ps-dell-price, [data-testid='price']")
                    if not price_el:
                        continue
                    price_text = await price_el.inner_text()
                    price_match = re.search(r'[\$]?([\d,]+\.?\d*)', price_text.replace(",", ""))
                    if not price_match:
                        continue
                    current_price = Decimal(price_match.group(1))

                    was_el = await item.query_selector(".strike-price, .original-price")
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
                        url=href if href.startswith("http") else f"https://www.dell.com{href}",
                        image_url=image_url,
                        current_price=current_price,
                        original_price=original_price if original_price and original_price > current_price else None,
                        category="Computers",
                        brand="Dell",
                        in_stock=True,
                        is_clearance=True,
                    ))
                except Exception as e:
                    self.logger.debug("Error parsing Dell Outlet item: %s", e)

        finally:
            await browser.close()
            await pw.stop()

        return products
