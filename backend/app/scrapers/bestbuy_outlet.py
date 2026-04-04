"""Best Buy Outlet scraper — clearance, open-box, refurbished."""

import re
from decimal import Decimal

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("bestbuy-outlet")
class BestBuyOutletScraper(PlaywrightScraper):
    retailer_slug = "bestbuy-outlet"
    rate_limit_seconds = 3.0

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            url = "https://www.bestbuy.com/site/electronics/outlet-refurbished-clearance/pcmcat142300050026.c?id=pcmcat142300050026"
            if not await self.safe_navigate(page, url):
                return products

            await page.wait_for_timeout(3000)
            items = await page.query_selector_all(".sku-item, [class*='sku-item'], .list-item")

            self.logger.info("Found %d Best Buy Outlet items", len(items))

            for item in items[:40]:
                try:
                    name_el = await item.query_selector(".sku-title a, .sku-header a")
                    if not name_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    href = await name_el.get_attribute("href") or ""

                    match = re.search(r'/(\d+)\.p', href)
                    external_id = f"bb-outlet-{match.group(1)}" if match else f"bb-outlet-{name[:20]}"

                    price_el = await item.query_selector(".priceView-customer-price span, [data-testid='customer-price'] span")
                    if not price_el:
                        continue
                    price_text = await price_el.inner_text()
                    price_match = re.search(r'[\$]?([\d,]+\.?\d*)', price_text.replace(",", ""))
                    if not price_match:
                        continue
                    current_price = Decimal(price_match.group(1))

                    was_el = await item.query_selector(".priceView-was-price, [data-testid='was-price']")
                    original_price = None
                    if was_el:
                        was_text = await was_el.inner_text()
                        was_match = re.search(r'[\$]?([\d,]+\.?\d*)', was_text.replace(",", ""))
                        if was_match:
                            original_price = Decimal(was_match.group(1))

                    img_el = await item.query_selector("img.product-image")
                    image_url = await img_el.get_attribute("src") if img_el else None

                    products.append(ScrapedProduct(
                        external_id=external_id,
                        name=name[:500],
                        url=href if href.startswith("http") else f"https://www.bestbuy.com{href}",
                        image_url=image_url,
                        current_price=current_price,
                        original_price=original_price if original_price and original_price > current_price else None,
                        category="Electronics",
                        in_stock=True,
                        is_clearance=True,
                    ))
                except Exception as e:
                    self.logger.debug("Error parsing BB Outlet item: %s", e)

        finally:
            await browser.close()
            await pw.stop()

        return products
