"""Base class for Playwright-based scrapers with anti-detection."""

import asyncio
import random
from typing import Optional

from app.scrapers.base import BaseScraper

# Realistic modern user agents — mix of Chrome, Firefox, Safari across Windows/Mac/Linux
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

# Corresponding Accept-Language headers to pair with UAs
_ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-US,en;q=0.8",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.9,fr;q=0.7",
]

# Viewport sizes drawn from real analytics data
_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 800},
    {"width": 2560, "height": 1440},
]


def _stealth_init_script() -> str:
    """JS injected before page load to mask automation fingerprints."""
    return """
    // Remove webdriver flag
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Fake plugins array (real browsers have plugins)
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' },
        ],
    });

    // Real browsers expose languages
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

    // Pass chrome runtime check
    window.chrome = { runtime: {} };

    // Prevent Notification.permission check from exposing automation
    const origQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : origQuery(parameters);
    """


class PlaywrightScraper(BaseScraper):
    scraper_type = "playwright"
    page_load_timeout: int = 30000
    rate_limit_seconds: float = 3.0

    async def _get_page(self):
        from playwright.async_api import async_playwright

        ua = random.choice(USER_AGENTS)
        viewport = random.choice(_VIEWPORTS)
        lang = random.choice(_ACCEPT_LANGUAGES)

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ],
        )
        context = await browser.new_context(
            user_agent=ua,
            viewport=viewport,
            locale="en-US",
            timezone_id="America/New_York",
            java_script_enabled=True,
            extra_http_headers={
                "Accept-Language": lang,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            },
        )

        # Inject stealth script before any page JS runs
        await context.add_init_script(_stealth_init_script())

        page = await context.new_page()

        # Block trackers and ads — speed + less fingerprinting surface
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,eot,mp4,webm}",
            lambda route: route.abort(),
        )
        await page.route(
            "**/google-analytics.com/**", lambda route: route.abort()
        )
        await page.route(
            "**/doubleclick.net/**", lambda route: route.abort()
        )

        return pw, browser, page

    async def safe_navigate(self, page, url: str) -> bool:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.page_load_timeout)
            # Human-like pause: random between 1.5–4s
            await asyncio.sleep(random.uniform(1.5, 4.0))
            # Simulate a short scroll to trigger lazy-loaded content
            await page.evaluate("window.scrollBy(0, random_scroll)")
            return True
        except Exception as e:
            self.logger.warning("Navigation failed for %s: %s", url, e)
            return False

    async def safe_navigate(self, page, url: str) -> bool:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.page_load_timeout)
            await asyncio.sleep(random.uniform(1.5, 4.0))
            # Gentle scroll to trigger lazy loads without looking robotic
            scroll_px = random.randint(200, 600)
            await page.evaluate(f"window.scrollBy(0, {scroll_px})")
            await asyncio.sleep(random.uniform(0.3, 0.8))
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
