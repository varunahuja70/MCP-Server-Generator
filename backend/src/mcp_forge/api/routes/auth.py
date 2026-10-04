"""Authentication endpoints for exposed mode: login with token and session cookie."""

import hmac

from fastapi import APIRouter, Depends, Request, Response

from mcp_forge.api.deps import get_current_settings, get_session_registry
from mcp_forge.api.schemas.models import LoginRequest, LoginResponse
from mcp_forge.config import Settings
from mcp_forge.errors import UnauthorizedError

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_current_settings),
) -> dict[str, str]:
    """Authenticate in exposed mode and obtain an HTTP-only session cookie."""
    if settings.forge_mode == "local":
        return {"status": "ok", "message": "Authentication not required in local mode"}

    if not settings.forge_access_token:
        raise UnauthorizedError("No access token configured on server.")

    # Constant time compare
    if not hmac.compare_digest(
        body.token.encode("utf-8"), settings.forge_access_token.encode("utf-8")
    ):
        raise UnauthorizedError("Invalid access token.")

    # Generate an opaque session token
    session_token = get_session_registry().create_session()

    # Set httpOnly cookie
    response.set_cookie(
        key="forge_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=(settings.env == "production"),
        path="/",
        max_age=86400,
    )

    return {"status": "ok", "message": "Logged in successfully"}


@router.get("/status")
async def auth_status(
    request: Request,
    settings: Settings = Depends(get_current_settings),
) -> dict[str, object]:
    """Get current auth status and server operating mode."""
    is_authenticated = settings.forge_mode == "local"
    if not is_authenticated:
        # Check if caller has valid session cookie or token
        cookie_val = request.cookies.get("forge_session", "").strip()
        if cookie_val and get_session_registry().validate_session(cookie_val):
            is_authenticated = True

    return {
        "authenticated": is_authenticated,
        "mode": settings.forge_mode,
        "playground_enabled": settings.playground_enabled,
    }


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, str]:
    """Clear session cookie and revoke session token."""
    cookie_val = request.cookies.get("forge_session", "").strip()
    if cookie_val:
        get_session_registry().revoke_session(cookie_val)
    response.delete_cookie(key="forge_session", path="/")
    return {"status": "ok", "message": "Logged out"}
