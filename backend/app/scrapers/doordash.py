"""DoorDash scraper — CRITICAL for catching $0.09 coffee-type glitches.

Monitors DoorDash store pages for items priced at absurd fractions of
their normal retail price. Compares DoorDash prices against known
retail equivalents in our own product database.
"""

import re
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper
from app.models.product import Product


@register_scraper("doordash")
class DoorDashScraper(PlaywrightScraper):
    retailer_slug = "doordash"
    rate_limit_seconds = 5.0

    # Popular store categories to monitor for glitches
    STORE_URLS = [
        "https://www.doordash.com/convenience/",
        "https://www.doordash.com/grocery/",
    ]

    # Known retail price references for common items
    KNOWN_RETAIL_RANGES = {
        "coffee": (3.0, 8.0),
        "energy drink": (2.0, 5.0),
        "milk": (3.0, 7.0),
        "bread": (2.0, 6.0),
        "eggs": (3.0, 8.0),
        "chips": (3.0, 7.0),
        "soda": (1.5, 3.0),
        "water": (1.0, 4.0),
        "beer": (8.0, 20.0),
        "wine": (8.0, 30.0),
        "detergent": (8.0, 20.0),
        "toilet paper": (5.0, 15.0),
        "paper towels": (5.0, 15.0),
    }

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            for store_url in self.STORE_URLS:
                try:
                    items = await self._scrape_store_page(page, store_url)
                    products.extend(items)
                except Exception as e:
                    self.logger.warning("Error scraping DoorDash page %s: %s", store_url, e)

        finally:
            await browser.close()
            await pw.stop()

        # Filter for potential glitches — items priced suspiciously low
        glitch_products = []
        for product in products:
            if self._is_potential_glitch(product):
                product.is_clearance = False  # Mark as glitch, not clearance
                glitch_products.append(product)
            elif product.original_price and product.current_price < product.original_price * Decimal("0.5"):
                glitch_products.append(product)

        self.logger.info("Found %d potential DoorDash glitches out of %d items", len(glitch_products), len(products))
        return glitch_products

    async def _scrape_store_page(self, page, url: str) -> list[ScrapedProduct]:
        products = []

        if not await self.safe_navigate(page, url):
            return products

        await page.wait_for_timeout(3000)

        # DoorDash uses various card layouts
        items = await page.query_selector_all(
            "[data-testid='StoreMenuItem'], "
            "[data-anchor-id*='MenuItem'], "
            ".sc-item-card, "
            "[class*='ItemCard']"
        )

        self.logger.info("Found %d DoorDash items on %s", len(items), url)

        for item in items[:60]:
            try:
                name_el = await item.query_selector(
                    "[data-testid='StoreMenuItemTitle'], "
                    "[class*='itemName'], "
                    "span[class*='title'], "
                    "h3, h4"
                )
                if not name_el:
                    continue
                name = (await name_el.inner_text()).strip()

                price_el = await item.query_selector(
                    "[data-testid='StoreMenuItemPrice'], "
                    "[class*='price'], "
                    "span[class*='Price']"
                )
                if not price_el:
                    continue
                price_text = await price_el.inner_text()
                price_match = re.search(r'[\$]?([\d,]+\.?\d*)', price_text.replace(",", ""))
                if not price_match:
                    continue
                current_price = Decimal(price_match.group(1))

                if current_price <= 0:
                    continue

                link_el = await item.query_selector("a")
                href = ""
                if link_el:
                    href = await link_el.get_attribute("href") or ""

                img_el = await item.query_selector("img")
                image_url = None
                if img_el:
                    image_url = await img_el.get_attribute("src")

                external_id = f"dd-{name[:30].replace(' ', '-').lower()}-{str(current_price)}"

                products.append(ScrapedProduct(
                    external_id=external_id,
                    name=f"[DoorDash] {name}"[:500],
                    url=href if href.startswith("http") else f"https://www.doordash.com{href}" if href else "https://www.doordash.com",
                    image_url=image_url,
                    current_price=current_price,
                    original_price=self._estimate_retail_price(name),
                    category="Delivery",
                    in_stock=True,
                ))
            except Exception as e:
                self.logger.debug("Error parsing DoorDash item: %s", e)

        return products

    def _is_potential_glitch(self, product: ScrapedProduct) -> bool:
        """Detect if a DoorDash item is priced at a glitch level."""
        # Items under $0.50 are almost certainly glitches
        if product.current_price < Decimal("0.50"):
            return True

        # Items ending in .01 or .09 that are unusually cheap
        cents = int(product.current_price * 100) % 100
        if cents in (1, 9) and product.current_price < Decimal("1.00"):
            return True

        # Compare against known retail ranges
        name_lower = product.name.lower()
        for keyword, (min_retail, max_retail) in self.KNOWN_RETAIL_RANGES.items():
            if keyword in name_lower:
                if float(product.current_price) < min_retail * 0.1:
                    return True

        return False

    def _estimate_retail_price(self, name: str) -> Optional[Decimal]:
        """Estimate the normal retail price based on product name."""
        name_lower = name.lower()
        for keyword, (min_retail, max_retail) in self.KNOWN_RETAIL_RANGES.items():
            if keyword in name_lower:
                avg = (min_retail + max_retail) / 2
                return Decimal(str(round(avg, 2)))
        return None
