"""Base class for API-based scrapers with aiohttp, adaptive rate limiting, and retry."""

import asyncio
import logging
import random
from typing import Any, Optional

import aiohttp

from app.scrapers.base import BaseScraper

# HTTP status codes that signal rate limiting or anti-bot blocking
_RATE_LIMIT_STATUSES = {429}
_BLOCK_STATUSES = {403, 503, 520, 521, 522, 523, 524}  # 52x = Cloudflare errors

# Phrases in response bodies that indicate blocking
_BLOCK_PHRASES = (b"captcha", b"access denied", b"rate limit", b"too many requests", b"cloudflare")

# Rotating user agents for HTTP scrapers — cover Chrome/Firefox/Safari across OS
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

_ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-US,en;q=0.8",
    "en-GB,en;q=0.9,en-US;q=0.8",
]


class ApiScraper(BaseScraper):
    scraper_type = "api"
    base_api_url: str = ""
    rate_limit_seconds: float = 1.0   # overridden at runtime from retailer.rate_limit_ms
    max_retries: int = 3
    timeout_seconds: int = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: float = 0.0
        # Rate-limit detection state
        self._backoff_multiplier: float = 1.0   # grows when blocked, resets on success
        self._consecutive_failures: int = 0
        self._rate_limited_until: float = 0.0   # asyncio loop time

    def _make_headers(self) -> dict:
        """Build a realistic browser header set with a rotated user agent."""
        ua = random.choice(_USER_AGENTS)
        lang = random.choice(_ACCEPT_LANGUAGES)
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": lang,
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        # Rotate session headers on each request to vary fingerprint
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._make_headers(),
            )
        return self._session

    def _rotate_session_headers(self) -> None:
        """Swap user agent mid-session — called after a rate-limit event."""
        if self._session and not self._session.closed:
            self._session.headers.update(self._make_headers())

    async def _enforce_rate_limit(self) -> None:
        """Wait out any active backoff period, then enforce the per-request delay."""
        loop_time = asyncio.get_event_loop().time()

        # Honor explicit backoff window first
        if loop_time < self._rate_limited_until:
            wait = self._rate_limited_until - loop_time
            self.logger.debug("In rate-limit backoff, sleeping %.1fs", wait)
            await asyncio.sleep(wait)

        # Apply per-request delay (scaled by backoff multiplier when degraded)
        effective = self.rate_limit_seconds * self._backoff_multiplier
        elapsed = asyncio.get_event_loop().time() - self._last_request_time
        if elapsed < effective:
            await asyncio.sleep(effective - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    def _is_rate_limited_response(self, status: int, headers: dict, body_prefix: bytes) -> bool:
        """Return True if the response looks like rate limiting or anti-bot blocking."""
        if status in _RATE_LIMIT_STATUSES:
            return True
        if status in _BLOCK_STATUSES:
            phrase_hit = any(p in body_prefix.lower() for p in _BLOCK_PHRASES)
            # 403 after prior successes, or 503 with a blocking phrase = blocked
            if self._consecutive_failures >= 1 or phrase_hit:
                return True
        return False

    def _handle_rate_limit(self, status: int, headers: dict, attempt: int) -> float:
        """Compute backoff duration, update state, and return seconds to sleep."""
        # Honour Retry-After if provided
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after:
            try:
                wait = float(retry_after)
            except ValueError:
                wait = 0.0
        else:
            wait = 0.0

        # Exponential backoff: 5s, 10s, 20s, 40s … capped at 120s, with jitter
        exp_wait = min(5.0 * (2 ** attempt), 120.0)
        wait = max(wait, exp_wait) + random.uniform(0, 2)

        # Grow the inter-request multiplier (up to 8×) so future requests are spaced out
        self._backoff_multiplier = min(self._backoff_multiplier * 2, 8.0)
        self._rate_limited_until = asyncio.get_event_loop().time() + wait
        self._consecutive_failures += 1

        self.logger.warning(
            "Rate limited / blocked (HTTP %d) on %s — backing off %.1fs (multiplier=%.1f×)",
            status, self.retailer_slug, wait, self._backoff_multiplier,
        )
        # Rotate user agent so the next request looks like a different browser
        self._rotate_session_headers()
        return wait

    def _handle_success(self) -> None:
        """Reset rate-limit state after a successful request."""
        if self._backoff_multiplier > 1.0:
            self.logger.info(
                "Back to normal after rate limiting (was %.1f× multiplier)", self._backoff_multiplier
            )
        self._backoff_multiplier = 1.0
        self._consecutive_failures = 0

    async def fetch_json(
        self, url: str, params: dict | None = None, headers: dict | None = None
    ) -> Any:
        """Fetch JSON with adaptive rate limiting and retry."""
        session = await self._get_session()

        for attempt in range(self.max_retries):
            await self._enforce_rate_limit()
            try:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        self._handle_success()
                        return await resp.json(content_type=None)

                    body_prefix = await resp.content.read(512)
                    resp_headers = dict(resp.headers)

                    if self._is_rate_limited_response(resp.status, resp_headers, body_prefix):
                        wait = self._handle_rate_limit(resp.status, resp_headers, attempt)
                        await asyncio.sleep(wait)
                    else:
                        self.logger.warning("HTTP %d from %s", resp.status, url)
                        self._consecutive_failures += 1
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.warning("Request error (attempt %d/%d): %s", attempt + 1, self.max_retries, e)
                self._consecutive_failures += 1
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None

    async def fetch_text(self, url: str, params: dict | None = None) -> str | None:
        """Fetch text with adaptive rate limiting and retry."""
        session = await self._get_session()

        for attempt in range(self.max_retries):
            await self._enforce_rate_limit()
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        self._handle_success()
                        return await resp.text()

                    body_prefix = await resp.content.read(512)
                    resp_headers = dict(resp.headers)

                    if self._is_rate_limited_response(resp.status, resp_headers, body_prefix):
                        wait = self._handle_rate_limit(resp.status, resp_headers, attempt)
                        await asyncio.sleep(wait)
                    else:
                        self._consecutive_failures += 1
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.warning("Request error (attempt %d/%d): %s", attempt + 1, self.max_retries, e)
                self._consecutive_failures += 1
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None

    async def cleanup(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def run(self, *args, **kwargs):
        # Read per-retailer rate limit from DB and apply it before scraping
        retailer = await self.get_retailer()
        if retailer and retailer.rate_limit_ms:
            self.rate_limit_seconds = retailer.rate_limit_ms / 1000.0
        try:
            return await super().run(*args, **kwargs)
        finally:
            await self.cleanup()
