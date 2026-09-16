# 🎯 Internship Radar — Automated Job Aggregation Pipeline

> A full-stack pipeline that scrapes **Greenhouse**, **Lever**, and **Ashby** ATS APIs for paid internships matching a Data Science / MLOps / SWE profile — then surfaces them in a live, searchable Next.js dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              RENDER (FastAPI Backend)             │
│                                                   │
│  GET /api/internships  ←─ SWR (5 min poll)       │
│         │                                         │
│  ┌──────▼──────────────────────────────────┐     │
│  │  Scraping Engine (asyncio.gather)        │     │
│  │  ├── Greenhouse  (~60 company slugs)     │     │
│  │  ├── Lever       (~50 company slugs)     │     │
│  │  └── Ashby       (~40 company slugs)     │     │
│  └──────┬───────────────────────────────────┘     │
│         │ Filter → Score → Dedup                  │
│  ┌──────▼───────────────────────────────────┐    │
│  │  TTL Cache (1h) → REST JSON response     │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              VERCEL (Next.js 14 Frontend)         │
│  • TanStack Table — sortable data grid            │
│  • FilterBar — search, work-mode, ATS, score      │
│  • ScoreBadge — color-coded match score           │
│  • SWR auto-poll every 5 min                      │
└─────────────────────────────────────────────────┘
```

---

## Features

- **Zero HTML parsing** — targets clean JSON APIs of Greenhouse, Lever, and Ashby
- **150+ company targets** — Anthropic, Cohere, Mistral, Stripe, Figma, Databricks, Perplexity, and more
- **Smart filtering** — paid-only, internship-type, geography (CA/US/UK/EU/SG + Remote), English-only
- **Tech score 0–100** — weighted against 60 DS/ML/SWE keywords (Python, MLOps, Docker, FastAPI, XGBoost…)
- **Stipend extraction** — regex-based salary/stipend parsing from job descriptions
- **Anti-bot** — 20-UA rotation, randomised delays, exponential backoff retry
- **Deduplication** — SHA-256 hash on company + title
- **1-hour TTL cache** — avoids hammering ATS APIs on every request
- **Memory-safe** — pure `httpx`, no Playwright; stays under Render's 512MB limit

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, httpx, Pydantic v2 |
| Scraping | httpx async (no Playwright) |
| Frontend | Next.js 14, TanStack Table v8, SWR, Tailwind CSS |
| Backend Deploy | Render (free/starter) |
| Frontend Deploy | Vercel (free) |

---

## Project Structure

```
job_scraper/
├── backend/
│   ├── main.py                 ← FastAPI app (3 endpoints)
│   ├── scraper/
│   │   ├── base.py             ← BaseScraper ABC with retry + UA rotation
│   │   ├── greenhouse.py       ← Greenhouse API scraper
│   │   ├── lever.py            ← Lever API scraper
│   │   ├── ashby.py            ← Ashby API scraper
│   │   └── manager.py          ← asyncio.gather() orchestrator
│   ├── parser/
│   │   ├── filters.py          ← 6 filter gate functions
│   │   └── scorer.py           ← Tech keyword weighted scorer
│   ├── models/schemas.py       ← Pydantic v2 models
│   ├── utils/
│   │   ├── cache.py            ← 1-hour TTL cache singleton
│   │   ├── dedup.py            ← SHA-256 deduplication
│   │   └── headers.py          ← UA rotation + HTTP headers
│   ├── requirements.txt        ← 5 pinned dependencies
│   ├── render.yaml             ← Render deployment config
│   └── Dockerfile              ← Multi-stage slim Docker build
└── frontend/
    ├── app/
    │   ├── layout.tsx           ← Dark-mode root layout
    │   ├── page.tsx             ← Main dashboard page
    │   └── globals.css
    ├── components/
    │   ├── JobTable.tsx         ← TanStack Table data grid
    │   ├── FilterBar.tsx        ← Live search + filter dropdowns
    │   └── ScoreBadge.tsx       ← Color-coded score with keyword tooltip
    ├── lib/api.ts               ← Typed SWR hook + refresh fn
    └── vercel.json              ← Vercel env config
```

---

## Quickstart

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 10000
```

```bash
# Test
curl http://localhost:10000/health
curl http://localhost:10000/api/internships
curl "http://localhost:10000/api/internships?min_score=50&work_mode=Remote"
curl http://localhost:10000/api/internships/refresh
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:10000" > .env.local
npm run dev
```

Open `http://localhost:3000`

---

## Deploy

### Render (Backend)

1. Connect repo at [render.com](https://render.com) → New Web Service
2. Set **Root Directory** to `backend`
3. Render auto-detects `render.yaml` — deploy ✅

### Vercel (Frontend)

1. Import repo at [vercel.com](https://vercel.com) → New Project
2. Set **Root Directory** to `frontend`
3. Add env var: `NEXT_PUBLIC_API_URL=https://your-service.onrender.com`
4. Deploy ✅

---

## API Reference

### `GET /api/internships`

| Param | Type | Description |
|-------|------|-------------|
| `min_score` | int 0–100 | Filter by minimum tech score |
| `work_mode` | string | `Remote` \| `Hybrid` \| `On-site` |
| `source` | string | `greenhouse` \| `lever` \| `ashby` |

### `GET /api/internships/refresh`
Force a fresh scrape, bypassing the cache.

### `GET /health`
Returns cache status and item count.

---

## Keyword Scoring

High-priority (3 pts): `Data Science`, `Machine Learning`, `MLOps`, `Python`, `SQL`, `Pandas`, `Scikit-learn`, `XGBoost`, `FastAPI`, `Docker`, `MLflow`

Medium (2 pts): `Java`, `Spring Boot`, `Microservices`, `PyTorch`, `TensorFlow`, `Spark`, `LLM`, `NLP`, `AWS/GCP/Azure`, `dbt`, `Airflow`

Score 70+ = 🟢 Strong match · 40–69 = 🟡 Partial · <40 = 🔴 Low

---

## Author

**Shayan Bhattacharjee** — Portfolio project demonstrating end-to-end pipeline engineering from ATS API scraping to full-stack deployment.
