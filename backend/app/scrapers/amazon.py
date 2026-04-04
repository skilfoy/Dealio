"""Amazon scraper with coupon detection.

Scrapes Today's Deals and Lightning Deals pages.
Detects coupon checkboxes and calculates true final price.
Optional: PA-API/Keepa/Rainforest integration when keys present.
"""

import re
from decimal import Decimal
from typing import Optional

from app.scrapers.playwright_base import PlaywrightScraper
from app.scrapers.base import ScrapedProduct
from app.scrapers.registry import register_scraper


@register_scraper("amazon")
class AmazonScraper(PlaywrightScraper):
    retailer_slug = "amazon"
    rate_limit_seconds = 5.0  # Very respectful to avoid bans

    DEAL_PAGES = [
        "https://www.amazon.com/deals?ref_=nav_cs_gb",
        "https://www.amazon.com/gp/goldbox?ref_=nav_cs_gb_td",
    ]

    async def scrape(self) -> list[ScrapedProduct]:
        products = []
        pw, browser, page = await self._get_page()

        try:
            for deal_url in self.DEAL_PAGES:
                try:
                    items = await self._scrape_deals_page(page, deal_url)
                    products.extend(items)
                except Exception as e:
                    self.logger.warning("Error scraping Amazon deal page: %s", e)

        finally:
            await browser.close()
            await pw.stop()

        seen = set()
        unique = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique.append(p)
        return unique

    async def _scrape_deals_page(self, page, url: str) -> list[ScrapedProduct]:
        products = []

        if not await self.safe_navigate(page, url):
            return products

        await page.wait_for_timeout(3000)

        # Find deal cards on the page
        deal_cards = await page.query_selector_all('[data-testid="deal-card"], .DealCard-module__dealCard, .a-section.a-spacing-none.tallCellView')

        self.logger.info("Found %d deal cards on Amazon", len(deal_cards))

        for card in deal_cards[:50]:  # Limit to first 50 for speed
            try:
                product = await self._parse_deal_card(page, card)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug("Error parsing Amazon deal card: %s", e)

        return products

    async def _parse_deal_card(self, page, card) -> Optional[ScrapedProduct]:
        # Extract product link
        link_el = await card.query_selector("a[href*='/dp/'], a[href*='/gp/product/']")
        if not link_el:
            return None

        href = await link_el.get_attribute("href") or ""
        asin = self._extract_asin(href)
        if not asin:
            return None

        # Extract name
        name_el = await card.query_selector(".a-truncate-full, .a-text-normal, [data-testid='product-title']")
        name = ""
        if name_el:
            name = (await name_el.inner_text()).strip()
        if not name:
            name = "Amazon Deal"

        # Extract prices
        price_el = await card.query_selector(".a-price .a-offscreen, .a-color-price, [data-testid='deal-price']")
        current_price = Decimal("0")
        if price_el:
            price_text = await price_el.inner_text()
            current_price = self._parse_price(price_text) or Decimal("0")

        original_el = await card.query_selector(".a-text-price .a-offscreen, .a-price[data-a-strike='true'] .a-offscreen, [data-testid='was-price']")
        original_price = None
        if original_el:
            orig_text = await original_el.inner_text()
            original_price = self._parse_price(orig_text)

        if current_price <= 0:
            return None

        # Extract image
        img_el = await card.query_selector("img")
        image_url = None
        if img_el:
            image_url = await img_el.get_attribute("src")

        # COUPON DETECTION — look for the coupon checkbox element
        coupon_code = None
        coupon_discount = None

        coupon_el = await card.query_selector(
            ".couponBadge, [data-testid='coupon-badge'], .s-coupon-highlight-color, "
            "[id*='coupon'], .a-color-success[class*='coupon']"
        )
        if coupon_el:
            coupon_text = await coupon_el.inner_text()
            coupon_code, coupon_discount = self._parse_coupon(coupon_text, current_price)

        url = f"https://www.amazon.com/dp/{asin}"

        return ScrapedProduct(
            external_id=asin,
            name=name[:500],
            url=url,
            image_url=image_url,
            current_price=current_price,
            original_price=original_price,
            coupon_code=coupon_code,
            coupon_discount=coupon_discount,
            in_stock=True,
        )

    def _extract_asin(self, url: str) -> Optional[str]:
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if match:
            return match.group(1)
        match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
        if match:
            return match.group(1)
        return None

    def _parse_price(self, text: str) -> Optional[Decimal]:
        if not text:
            return None
        match = re.search(r'\$?([\d,]+\.?\d*)', text.replace(",", ""))
        if match:
            try:
                return Decimal(match.group(1))
            except Exception:
                pass
        return None

    def _parse_coupon(self, text: str, current_price: Decimal) -> tuple[Optional[str], Optional[Decimal]]:
        """Parse coupon text like 'Save 20%' or 'Save $10.00'."""
        text = text.lower()

        # Percentage coupon: "save 20% with coupon"
        pct_match = re.search(r'(\d+)%', text)
        if pct_match:
            pct = int(pct_match.group(1))
            discount = current_price * Decimal(str(pct)) / Decimal("100")
            return f"{pct}% coupon", discount.quantize(Decimal("0.01"))

        # Fixed amount: "save $10.00 with coupon"
        amt_match = re.search(r'\$(\d+\.?\d*)', text)
        if amt_match:
            discount = Decimal(amt_match.group(1))
            return f"${discount} coupon", discount

        return None, None
