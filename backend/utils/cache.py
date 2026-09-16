"""In-memory TTL cache for scrape results.

On Render free tier, the process restarts on cold-start so the cache
is intentionally ephemeral. The 1-hour TTL prevents hammering ATS APIs
on every request within a single process lifetime.
"""
from __future__ import annotations

import asyncio
import time
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TTLCache:
    """Thread-safe async-compatible in-memory cache with TTL expiry."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._data: Any = None
        self._timestamp: float = 0.0
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()

    def is_fresh(self) -> bool:
        return self._data is not None and (time.monotonic() - self._timestamp) < self._ttl

    def get(self) -> Any | None:
        return self._data if self.is_fresh() else None

    def set(self, data: Any) -> None:
        self._data = data
        self._timestamp = time.monotonic()
        count = len(data) if isinstance(data, list) else 1
        logger.info(f"Cache updated — {count} items stored (TTL {self._ttl}s)")

    def invalidate(self) -> None:
        self._data = None
        self._timestamp = 0.0
        logger.info("Cache invalidated")

    @property
    def age_seconds(self) -> float:
        if self._timestamp == 0:
            return float("inf")
        return time.monotonic() - self._timestamp

    @property
    def item_count(self) -> int:
        data = self._data
        if data is None:
            return 0
        return len(data) if isinstance(data, list) else 1


# Module-level singleton
job_cache = TTLCache(ttl_seconds=3600)
