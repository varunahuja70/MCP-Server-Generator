"""Shared FastAPI route dependencies: DB sessions and authentication checks."""

import hmac
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.config import Settings
from mcp_forge.db.session import get_db_session
from mcp_forge.errors import UnauthorizedError


def get_current_settings(request: Request) -> Settings:
    """Retrieve app settings from request state."""
    settings: Settings = request.app.state.settings
    return settings


async def get_db(
    settings: Settings = Depends(get_current_settings),
) -> AsyncGenerator[AsyncSession]:
    """Dependency for obtaining an async DB session."""
    async with get_db_session(settings) as session:
        yield session


def require_auth(request: Request, settings: Settings = Depends(get_current_settings)) -> None:
    """Validate authentication. In local mode, access is free. In exposed mode, require token or session cookie."""
    if settings.forge_mode == "local":
        return

    # In exposed mode, check Authorization header (Bearer) or session cookie
    token = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "forge_session" in request.cookies:
        token = request.cookies.get("forge_session", "").strip()

    if not token or not settings.forge_access_token:
        raise UnauthorizedError(
            "Authentication required in exposed mode.", details={"mode": "exposed"}
        )

    # Constant-time comparison
    if not hmac.compare_digest(token.encode("utf-8"), settings.forge_access_token.encode("utf-8")):
        raise UnauthorizedError("Invalid access token.", details={"mode": "exposed"})
