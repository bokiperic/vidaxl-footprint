"""Security utilities: API key auth, login auth, rate limiting, security headers."""
from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response

from src.config import settings

# --- Session Token Helpers ---

_SESSION_COOKIE = "session_token"
_SESSION_MAX_AGE = 86400 * 7  # 7 days


def _make_token(username: str) -> str:
    """Create an HMAC-signed session token."""
    msg = f"{username}:{settings.AUTH_SECRET}".encode()
    return hmac.new(settings.AUTH_SECRET.encode(), msg, hashlib.sha256).hexdigest()


def _verify_token(token: str) -> bool:
    """Verify a session token matches the expected value."""
    expected = _make_token(settings.AUTH_USERNAME)
    return hmac.compare_digest(token, expected)

# --- API Key Authentication ---

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(request: Request, api_key: str | None = Security(_api_key_header)):
    """Dependency that enforces API key auth in production.

    Allows through if the user has a valid session cookie (logged in via browser)
    or a valid X-API-Key header (programmatic access).
    """
    if not settings.is_production:
        return
    # Allow logged-in browser users
    token = request.cookies.get(_SESSION_COOKIE)
    if token and _verify_token(token):
        return
    # Check API key for programmatic access
    if not settings.API_KEY:
        return
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


# --- Login Gate Middleware ---

# Paths that don't require login
_PUBLIC_PATHS = {"/login", "/logout"}


class LoginRequiredMiddleware(BaseHTTPMiddleware):
    """Redirect unauthenticated browser requests to the login page."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth entirely if credentials are not configured
        if not settings.AUTH_USERNAME or not settings.AUTH_PASSWORD:
            return await call_next(request)

        # Allow public paths
        if path in _PUBLIC_PATHS:
            return await call_next(request)

        # Allow requests with valid API key (programmatic access)
        if settings.API_KEY and request.headers.get("X-API-Key") == settings.API_KEY:
            return await call_next(request)

        # Check session cookie
        token = request.cookies.get(_SESSION_COOKIE)
        if token and _verify_token(token):
            return await call_next(request)

        # Not authenticated — redirect browsers, 401 for API calls
        if "text/html" in request.headers.get("accept", ""):
            return RedirectResponse(url="/login", status_code=302)
        return Response(
            content='{"detail":"Authentication required"}',
            status_code=401,
            media_type="application/json",
        )


# --- Rate Limiting Middleware ---

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter for POST endpoints."""

    def __init__(self, app, max_calls: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            window_start = now - self.window_seconds

            # Clean old entries and check limit
            self._requests[client_ip] = [
                t for t in self._requests[client_ip] if t > window_start
            ]

            if len(self._requests[client_ip]) >= self.max_calls:
                return Response(
                    content='{"detail":"Rate limit exceeded. Try again later."}',
                    status_code=429,
                    media_type="application/json",
                )

            self._requests[client_ip].append(now)

        return await call_next(request)


# --- Security Headers Middleware ---

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        return response
