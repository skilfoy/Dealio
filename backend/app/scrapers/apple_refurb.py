"""Apple Refurbished Store scraper."""

import re
from decimal import Decimal
from typing import Optional

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("apple-refurb")
class AppleRefurbScraper(PlaywrightScraper):
    retailer_slug = "apple-refurb"
    rate_limit_seconds = 3.0

    CATEGORIES = [
        "https://www.apple.com/shop/refurbished/mac",
        "https://www.apple.com/shop/refurbished/ipad",
        "https://www.apple.com/shop/refurbished/watch",
        "https://www.apple.com/shop/refurbished/airpods",
    ]

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            for url in self.CATEGORIES:
                try:
                    if not await self.safe_navigate(page, url):
                        continue
                    await page.wait_for_timeout(2000)

                    items = await page.query_selector_all(".rf-refurb-category-grid-no-498 li, .as-price-currentprice, [class*='product-tile']")
                    self.logger.info("Found %d Apple Refurb items on %s", len(items), url)

                    for item in items[:20]:
                        try:
                            name_el = await item.query_selector("h3 a, .rf-refurb-producttile-link")
                            if not name_el:
                                continue
                            name = (await name_el.inner_text()).strip()
                            href = await name_el.get_attribute("href") or ""

                            match = re.search(r'/([A-Z0-9]+)$', href)
                            external_id = match.group(1) if match else name[:30]

                            price_el = await item.query_selector(".as-price-currentprice, .rf-refurb-producttile-price .current_price")
                            if not price_el:
                                continue
                            price_text = await price_el.inner_text()
                            price_match = re.search(r'[\$]?([\d,]+\.?\d*)', price_text.replace(",", ""))
                            if not price_match:
                                continue
                            current_price = Decimal(price_match.group(1))

                            # Apple refurb savings are typically 15-30% off original
                            savings_el = await item.query_selector(".as-price-previousprice, .rf-refurb-producttile-savings")
                            original_price = None
                            if savings_el:
                                sav_text = await savings_el.inner_text()
                                sav_match = re.search(r'[\$]?([\d,]+\.?\d*)', sav_text.replace(",", ""))
                                if sav_match:
                                    original_price = Decimal(sav_match.group(1))

                            products.append(ScrapedProduct(
                                external_id=f"apple-{external_id}",
                                name=name[:500],
                                url=href if href.startswith("http") else f"https://www.apple.com{href}",
                                current_price=current_price,
                                original_price=original_price if original_price and original_price > current_price else None,
                                category="Apple",
                                brand="Apple",
                                in_stock=True,
                                is_clearance=True,
                            ))
                        except Exception as e:
                            self.logger.debug("Error parsing Apple Refurb item: %s", e)
                except Exception as e:
                    self.logger.warning("Error scraping Apple Refurb %s: %s", url, e)

        finally:
            await browser.close()
            await pw.stop()

        return products
