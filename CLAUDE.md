# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Start PostgreSQL
docker-compose up db -d

# Create venv (requires Python 3.12+)
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start dev server (with reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Full stack via Docker
docker-compose up --build

# Run tests
pytest tests/ -v
```

**Key URLs:** Dashboard at `/dashboard`, API docs at `/docs`, root `/` shows app info + mock_mode status.

## Architecture

**Async Python stack:** FastAPI + SQLAlchemy 2.0 async + asyncpg + httpx. All DB operations and HTTP calls are async.

### Scraper Registry Pattern
Scrapers self-register via decorator in `src/scrapers/registry.py`:
```python
@register("trustpilot")
class TrustpilotScraper(BaseScraper): ...
```
`src/scrapers/__init__.py` imports all scraper modules to trigger registration. The `scraper_service` looks up scrapers by `source.scraper_key` from the `SCRAPER_REGISTRY` dict. To add a new scraper: create the file, inherit `BaseScraper`, decorate with `@register("key")`, import in `__init__.py`, and add a source row to the DB.

### Analysis Pipeline (3 stages)
`src/analysis/pipeline.py` orchestrates:
1. **Sentiment** — batch reviews (30/call) to Claude Sonnet → POS/NEU/NEG + score + topic tags. Stored on review rows.
2. **Themes** — aggregate topic frequencies, Claude merges synonyms → top 10 complaints. Stored as `analysis_results`.
3. **Trends** — monthly sentiment data → Claude Opus for trends + 5 recommendations. Stored as `analysis_results`.

**Mock mode** (`src/analysis/mock.py`): activates automatically when `ANTHROPIC_API_KEY` is empty. Uses keyword matching for sentiment and returns static mock data for themes/trends. Allows full development without API costs.

### Background Tasks
Scraping and analysis run via FastAPI `BackgroundTasks`. Background tasks create their own `async_session` instances (not the request-scoped one).

### Database Upsert
Reviews/articles use `ON CONFLICT (source_id, external_id) DO UPDATE` for safe re-scraping and dedup.

### Frontend
`dashboard/` is plain HTML + vanilla JS + Chart.js (CDN). Served as static files by FastAPI. No build step.

## Configuration

All config via environment variables (`.env` file), managed by Pydantic `BaseSettings` in `src/config.py`. The `use_mock_analysis` property auto-switches between mock and Claude based on whether `ANTHROPIC_API_KEY` is set.

## Database

PostgreSQL 16. Connection: `vidaxl:vidaxl@localhost:5432/vidaxl_footprint`. Six tables: `sources`, `reviews`, `articles`, `scrape_runs`, `analysis_runs`, `analysis_results`. Initial migration seeds 16 sources (13 Trustpilot regions + ReviewsIO + PissedConsumer + VidaXL Blog). Connect via: `docker exec -it vidaxl-footprint-db-1 psql -U vidaxl -d vidaxl_footprint`.
