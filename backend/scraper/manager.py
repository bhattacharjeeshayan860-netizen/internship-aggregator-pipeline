"""Scraper orchestrator — runs all scrapers concurrently via asyncio.gather."""
from __future__ import annotations

import asyncio
import logging
from typing import Type

from .greenhouse import GreenhouseScraper
from .lever import LeverScraper
from .ashby import AshbyScraper
from .base import BaseScraper

logger = logging.getLogger(__name__)

SCRAPERS: list[Type[BaseScraper]] = [
    GreenhouseScraper,
    LeverScraper,
    AshbyScraper,
]

# Per-scraper timeout — now 120s since concurrent fetch is fast but
# Render free-tier network can be slow on cold start
SCRAPER_TIMEOUT = 120.0


async def _run_one(ScraperClass: Type[BaseScraper]) -> list[dict]:
    """Run a single scraper class, returning [] on failure."""
    try:
        async with ScraperClass() as scraper:
            return await asyncio.wait_for(scraper.fetch(), timeout=SCRAPER_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error(f"[{ScraperClass.NAME}] timed out after {SCRAPER_TIMEOUT}s")
        return []
    except Exception as exc:
        logger.error(f"[{ScraperClass.NAME}] crashed: {exc}")
        return []


async def run_all_scrapers() -> list[dict]:
    """
    Runs all scrapers concurrently and merges their results.

    Returns a flat list of raw job dicts ready for filtering and scoring.
    Each dict contains at minimum: source, company, title, location,
    apply_url, description, posted_date.
    """
    logger.info(f"Starting concurrent scrape across {len(SCRAPERS)} ATS platforms…")
    results = await asyncio.gather(*[_run_one(cls) for cls in SCRAPERS])

    merged: list[dict] = []
    for batch in results:
        merged.extend(batch)

    logger.info(f"Scrape complete — {len(merged)} raw jobs collected")
    return merged
