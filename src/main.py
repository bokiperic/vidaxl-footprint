import logging
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from src.api.scraper_control import router as scraper_router
from src.api.reviews import router as reviews_router
from src.api.articles import router as articles_router
from src.api.analysis import router as analysis_router
from src.api.dashboard import router as dashboard_router
from src.config import settings
from src.security import (
    LoginRequiredMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    _SESSION_COOKIE,
    _SESSION_MAX_AGE,
    _make_token,
)

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Hunkemoller Digital Footprint",
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# Security middleware (order matters — outermost runs first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_calls=10, window_seconds=60)
app.add_middleware(LoginRequiredMiddleware)

dashboard_dir = Path(__file__).parent.parent / "dashboard"


# --- Login / Logout ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    error = request.query_params.get("error", "")
    return FileResponse(str(dashboard_dir / "login.html")) if not error else HTMLResponse(
        (dashboard_dir / "login.html").read_text().replace("<!--ERROR-->", '<p class="error">Invalid username or password</p>'),
    )


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == settings.AUTH_USERNAME and password == settings.AUTH_PASSWORD:
        token = _make_token(username)
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key=_SESSION_COOKIE,
            value=token,
            max_age=_SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
        )
        return response
    return RedirectResponse(url="/login?error=1", status_code=303)


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(_SESSION_COOKIE)
    return response


# --- App routes ---

app.include_router(scraper_router)
app.include_router(reviews_router)
app.include_router(articles_router)
app.include_router(analysis_router)
app.include_router(dashboard_router)

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
    }
