"""Base class for API-based scrapers with aiohttp, rate limiting, and retry."""

import asyncio
import logging
from typing import Any, Optional

import aiohttp

from app.scrapers.base import BaseScraper


class ApiScraper(BaseScraper):
    scraper_type = "api"
    base_api_url: str = ""
    rate_limit_seconds: float = 1.0
    max_retries: int = 3
    timeout_seconds: int = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: float = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": "DealRadar/1.0 (Deal Monitoring Service)"},
            )
        return self._session

    async def _rate_limit(self) -> None:
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            await asyncio.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def fetch_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> Any:
        """Fetch JSON with rate limiting and retry."""
        session = await self._get_session()

        for attempt in range(self.max_retries):
            await self._rate_limit()
            try:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        wait = 2 ** (attempt + 1)
                        self.logger.warning("Rate limited on %s, waiting %ds", url, wait)
                        await asyncio.sleep(wait)
                    else:
                        self.logger.warning("HTTP %d from %s", resp.status, url)
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.warning("Request error on attempt %d: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None

    async def fetch_text(self, url: str, params: dict | None = None) -> str | None:
        session = await self._get_session()

        for attempt in range(self.max_retries):
            await self._rate_limit()
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        return await resp.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.warning("Request error on attempt %d: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        return None

    async def cleanup(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def run(self, *args, **kwargs):
        try:
            return await super().run(*args, **kwargs)
        finally:
            await self.cleanup()
