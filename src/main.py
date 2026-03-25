import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.scraper_control import router as scraper_router
from src.api.reviews import router as reviews_router
from src.api.articles import router as articles_router
from src.api.analysis import router as analysis_router
from src.api.dashboard import router as dashboard_router
from src.config import settings

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Hunkemoller Digital Footprint", version="0.1.0")

app.include_router(scraper_router)
app.include_router(reviews_router)
app.include_router(articles_router)
app.include_router(analysis_router)
app.include_router(dashboard_router)

# Serve static dashboard files
dashboard_dir = Path(__file__).parent.parent / "dashboard"
if dashboard_dir.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_dir)), name="static")


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(str(dashboard_dir / "index.html"))


@app.get("/")
async def root():
    return {
        "app": "Hunkemoller Digital Footprint",
        "version": "0.1.0",
        "dashboard": "/dashboard",
        "docs": "/docs",
        "mock_mode": settings.use_mock_analysis,
    }
