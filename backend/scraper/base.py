"""Abstract base scraper with httpx async client, UA rotation, retry + backoff."""
from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Any

import httpx

from utils.headers import get_headers

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    NAME: str = "base"
    REQUEST_TIMEOUT: float = 15.0
    MAX_RETRIES: int = 3

    def __init__(self) -> None:
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BaseScraper":
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.REQUEST_TIMEOUT),
            follow_redirects=True,
            # http2=True,  # uncomment if httpx[http2] is installed
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self.client:
            await self.client.aclose()

    async def _get(self, url: str, **kwargs: Any) -> dict[str, Any] | list:
        """GET with UA rotation and exponential-backoff retry.

        Delays only happen between retries (not on every request).
        Concurrency throttling is handled by the caller via asyncio.Semaphore.
        404 responses are treated as a dead slug — logged at DEBUG and returned
        immediately without wasting retry budget.
        """
        last_exc: Exception | None = None
        broke_early = False

        for attempt in range(self.MAX_RETRIES):
            try:
                resp = await self.client.get(url, headers=get_headers(), **kwargs)  # type: ignore[union-attr]
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status = exc.response.status_code
                if status == 404:
                    # Dead slug — not worth retrying
                    logger.debug(f"[{self.NAME}] 404 (invalid slug): {url}")
                    broke_early = True
                    break
                if status == 429 or status >= 500:
                    wait = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"[{self.NAME}] HTTP {status} on {url} — retry in {wait:.1f}s")
                    await asyncio.sleep(wait)
                else:
                    logger.warning(f"[{self.NAME}] HTTP {status} for {url} — skipping")
                    broke_early = True
                    break
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                wait = 2 ** attempt
                logger.warning(f"[{self.NAME}] Network error on {url} — retry in {wait}s: {exc}")
                await asyncio.sleep(wait)
            except Exception as exc:
                last_exc = exc
                logger.error(f"[{self.NAME}] Unexpected error for {url}: {exc}")
                broke_early = True
                break

        if not broke_early:
            logger.warning(f"[{self.NAME}] Retries exhausted for {url}")
        return {}

    async def _post(self, url: str, json: dict, **kwargs: Any) -> dict[str, Any] | list:
        """POST with retry logic (used for GraphQL/Ashby endpoints)."""
        last_exc: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            try:
                await asyncio.sleep(random.uniform(0.5, 2.0))
                resp = await self.client.post(url, headers=get_headers(), json=json, **kwargs)  # type: ignore[union-attr]
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_exc = exc
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
        logger.error(f"[{self.NAME}] POST failed {url}: {last_exc}")
        return {}

    @abstractmethod
    async def fetch(self) -> list[dict]:
        """Return a list of normalised raw job dicts."""
        ...
