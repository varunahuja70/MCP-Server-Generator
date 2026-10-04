"""Security middleware for MCP Forge FastAPI application."""

from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_forge.config import Settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects strict defensive HTTP security headers on all responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["Referrer-Policy"] = "same-origin"
        headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
        return response


def normalize_host(host_header: str) -> str:
    """Extract normalized hostname without port, safely handling IPv6 brackets and ports."""
    header = host_header.strip()
    if not header:
        return ""
    if header.startswith("["):
        # Bracketed IPv6 address, e.g. [::1] or [::1]:8080
        end_idx = header.find("]")
        if end_idx != -1:
            return header[1:end_idx].lower()
        return header.lower()
    if ":" in header:
        parts = header.split(":")
        if len(parts) == 2:
            # Single colon denotes host:port
            return parts[0].strip().lower()
        # Multiple colons without brackets denotes bare IPv6 address like ::1
        return header.lower()
    return header.lower()


class HostAllowlistMiddleware(BaseHTTPMiddleware):
    """Enforces strict Host header allowlist to prevent DNS-rebinding attacks."""

    def __init__(self, app: Any, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        allowed: set[str] = {"localhost", "127.0.0.1", "::1", "[::1]"}
        if settings.forge_host:
            h = settings.forge_host.lower().strip("[]")
            allowed.add(h)
            allowed.add(settings.forge_host.lower())
        if settings.forge_public_host:
            h = settings.forge_public_host.lower().strip("[]")
            allowed.add(h)
            allowed.add(settings.forge_public_host.lower())
        self.allowed_hosts = allowed

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        host_header = request.headers.get("host", "")
        host_only = normalize_host(host_header)

        if not host_only or (
            host_only not in self.allowed_hosts and f"[{host_only}]" not in self.allowed_hosts
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "INVALID_HOST",
                        "message": f"Host '{host_header}' is not permitted by security policy.",
                        "details": {"host": host_header},
                    }
                },
            )

        return await call_next(request)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Requires custom X-Forge-Request header and validates Origin on mutation requests."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    EXEMPT_PATHS = {"/healthz", "/readyz", "/version"}

    def __init__(self, app: Any, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        allowed: set[str] = {"localhost", "127.0.0.1", "::1", "[::1]"}
        if settings.forge_host:
            h = settings.forge_host.lower().strip("[]")
            allowed.add(h)
            allowed.add(settings.forge_host.lower())
        if settings.forge_public_host:
            h = settings.forge_public_host.lower().strip("[]")
            allowed.add(h)
            allowed.add(settings.forge_public_host.lower())
        self.allowed_hosts = allowed

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in self.SAFE_METHODS or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Validate X-Forge-Request custom header
        forge_header = request.headers.get("X-Forge-Request")
        if forge_header != "1":
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "MISSING_FORGE_HEADER",
                        "message": "State-changing requests must include header 'X-Forge-Request: 1'.",
                        "details": {},
                    }
                },
            )

        # Validate Origin header if present
        origin = request.headers.get("origin")
        if origin:
            parsed = urlparse(origin)
            origin_host = (parsed.hostname or "").lower().strip("[]")
            if (
                origin_host not in self.allowed_hosts
                and f"[{origin_host}]" not in self.allowed_hosts
            ):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {
                            "code": "INVALID_ORIGIN",
                            "message": f"Origin '{origin}' is not permitted by security policy.",
                            "details": {"origin": origin},
                        }
                    },
                )

        return await call_next(request)
