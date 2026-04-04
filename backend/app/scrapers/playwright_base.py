"""Base class for Playwright-based scrapers with anti-detection."""

import asyncio
import random
from typing import Optional

from app.scrapers.base import BaseScraper

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]


class PlaywrightScraper(BaseScraper):
    scraper_type = "playwright"
    page_load_timeout: int = 30000
    rate_limit_seconds: float = 3.0

    async def _get_page(self):
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": random.randint(1280, 1920), "height": random.randint(800, 1080)},
            locale="en-US",
        )
        page = await context.new_page()

        # Block unnecessary resources for speed
        await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,eot}", lambda route: route.abort())

        return pw, browser, page

    async def safe_navigate(self, page, url: str) -> bool:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.page_load_timeout)
            await asyncio.sleep(random.uniform(1, 2))
            return True
        except Exception as e:
            self.logger.warning("Navigation failed for %s: %s", url, e)
            return False

    async def extract_text(self, page, selector: str) -> Optional[str]:
        try:
            el = await page.query_selector(selector)
            if el:
                return (await el.inner_text()).strip()
        except Exception:
            pass
        return None

    async def extract_attribute(self, page, selector: str, attr: str) -> Optional[str]:
        try:
            el = await page.query_selector(selector)
            if el:
                return await el.get_attribute(attr)
        except Exception:
            pass
        return None

    async def run(self, *args, **kwargs):
        return await super().run(*args, **kwargs)
