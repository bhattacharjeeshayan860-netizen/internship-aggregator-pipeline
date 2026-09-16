"""
Internship Aggregator — FastAPI Backend
=======================================
Endpoints:
  GET /health                    — service + cache health
  GET /api/internships           — return cached (or fresh) job listings
  GET /api/internships/refresh   — force fresh scrape, bypass cache

Query params for /api/internships:
  min_score  int   filter by minimum tech_score (0–100)
  work_mode  str   "Remote" | "Hybrid" | "On-site"
  source     str   "greenhouse" | "lever" | "ashby"
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import JobListing, ScrapeResult
from parser.filters import passes_all_filters, determine_work_mode
from parser.scorer import score_job
from scraper.manager import run_all_scrapers
from utils.cache import job_cache
from utils.dedup import deduplicate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("internship_api")

# ── Pipeline ─────────────────────────────────────────────────────────────────


async def build_job_listings() -> list[JobListing]:
    """Full pipeline: scrape → filter → dedup → score → sort."""
    raw_jobs = await run_all_scrapers()

    # 1. Filter
    filtered = [j for j in raw_jobs if passes_all_filters(j)]
    logger.info(f"Filter: {len(filtered)}/{len(raw_jobs)} jobs passed")

    # 2. Deduplicate
    unique = deduplicate(filtered)

    # 3. Score + build structured models
    listings: list[JobListing] = []
    for job in unique:
        scored = score_job(job)
        listings.append(
            JobListing(
                id=job["id"],
                company=job.get("company", ""),
                title=job.get("title", ""),
                location=job.get("location", ""),
                work_mode=determine_work_mode(
                    job.get("location", ""), job.get("description", "")
                ),
                tech_score=scored.tech_score,
                matched_keywords=scored.matched_keywords,
                stipend_estimate=scored.stipend_estimate,
                apply_url=job.get("apply_url", ""),
                source=job.get("source", ""),
                posted_date=job.get("posted_date") or None,
            )
        )

    # 4. Sort by score descending, then alphabetically by company
    listings.sort(key=lambda j: (-j.tech_score, j.company.lower()))
    return listings


# ── Lifespan: warm cache on startup ──────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — warming job cache (120s budget)…")
    try:
        jobs = await asyncio.wait_for(build_job_listings(), timeout=120)
        job_cache.set(jobs)
        logger.info(f"Cache warm: {len(jobs)} internships ready")
    except asyncio.TimeoutError:
        logger.warning("Startup scrape timed out — cache warmed on first request")
    except Exception as exc:
        logger.error(f"Startup scrape failed: {exc}")
    yield
    logger.info("Shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Internship Aggregator API",
    description=(
        "Scrapes Greenhouse, Lever, and Ashby ATS platforms for paid internships "
        "matching a Data Science / MLOps / SWE profile."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow Vercel frontend + local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten to your Vercel domain in production
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/health", tags=["ops"])
async def health():
    """Service health check — returns cache status."""
    return {
        "status": "ok",
        "cached_jobs": job_cache.item_count,
        "cache_fresh": job_cache.is_fresh(),
        "cache_age_seconds": round(job_cache.age_seconds, 1),
    }


@app.get("/api/internships", response_model=ScrapeResult, tags=["internships"])
async def get_internships(
    min_score: int = Query(default=0, ge=0, le=100, description="Minimum tech match score"),
    work_mode: Optional[str] = Query(default=None, description="Remote | Hybrid | On-site"),
    source: Optional[str] = Query(default=None, description="greenhouse | lever | ashby"),
):
    """
    Return internship listings. Serves from cache if fresh (< 1h old),
    otherwise triggers a background scrape and waits.
    """
    cached = job_cache.get()
    if cached is not None:
        jobs: list[JobListing] = cached
        cache_hit = True
    else:
        logger.info("Cache miss — running fresh scrape…")
        try:
            jobs = await asyncio.wait_for(build_job_listings(), timeout=90)
            job_cache.set(jobs)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=503,
                detail="Scrape timed out — try again in a few seconds.",
            )
        cache_hit = False

    # Apply optional query filters server-side
    if min_score > 0:
        jobs = [j for j in jobs if j.tech_score >= min_score]
    if work_mode:
        jobs = [j for j in jobs if j.work_mode.lower() == work_mode.lower()]
    if source:
        jobs = [j for j in jobs if j.source.lower() == source.lower()]

    return ScrapeResult(
        jobs=jobs,
        total=len(jobs),
        scraped_at=datetime.now(timezone.utc),
        cache_hit=cache_hit,
    )


@app.get("/api/internships/refresh", response_model=ScrapeResult, tags=["internships"])
async def refresh_internships():
    """Force a fresh scrape, bypassing the TTL cache entirely."""
    job_cache.invalidate()
    try:
        jobs = await asyncio.wait_for(build_job_listings(), timeout=120)
        job_cache.set(jobs)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Scrape timed out.")

    return ScrapeResult(
        jobs=jobs,
        total=len(jobs),
        scraped_at=datetime.now(timezone.utc),
        cache_hit=False,
    )
