import hashlib
import hmac
import secrets
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.config import Settings
from mcp_forge.db.session import get_db_session
from mcp_forge.errors import UnauthorizedError


@dataclass
class AuthSession:
    token: str
    created_at: float
    expires_at: float
    last_used: float


class SessionRegistry:
    """In-memory session registry with expiration for opaque session tokens."""

    def __init__(self, ttl_seconds: float = 86400.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, AuthSession] = {}

    def create_session(self) -> str:
        token = secrets.token_urlsafe(32)
        now = time.time()
        self._sessions[token] = AuthSession(
            token=token,
            created_at=now,
            expires_at=now + self.ttl_seconds,
            last_used=now,
        )
        return token

    def validate_session(self, token: str) -> bool:
        self.purge_expired()
        session = self._sessions.get(token)
        if not session:
            return False
        if time.time() > session.expires_at:
            self._sessions.pop(token, None)
            return False
        session.last_used = time.time()
        return True

    def revoke_session(self, token: str) -> None:
        self._sessions.pop(token, None)

    def purge_expired(self) -> None:
        now = time.time()
        expired = [t for t, s in self._sessions.items() if now > s.expires_at]
        for t in expired:
            self._sessions.pop(t, None)


_SESSION_REGISTRY = SessionRegistry()


def get_session_registry() -> SessionRegistry:
    return _SESSION_REGISTRY


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


def require_auth(request: Request, settings: Settings = Depends(get_current_settings)) -> str:
    """Validate authentication. In local mode, access is free. In exposed mode, require token or session cookie."""
    if settings.forge_mode == "local":
        request.state.principal = "local"
        return "local"

    if not settings.forge_access_token:
        raise UnauthorizedError(
            "Authentication required in exposed mode.", details={"mode": "exposed"}
        )

    # 1. Check Authorization header (Bearer)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if hmac.compare_digest(token.encode("utf-8"), settings.forge_access_token.encode("utf-8")):
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]
            principal = f"bearer:{token_hash}"
            request.state.principal = principal
            return principal
        raise UnauthorizedError("Invalid access token.", details={"mode": "exposed"})

    # 2. Check forge_session cookie
    if "forge_session" in request.cookies:
        cookie_val = request.cookies.get("forge_session", "").strip()
        if cookie_val and _SESSION_REGISTRY.validate_session(cookie_val):
            token_hash = hashlib.sha256(cookie_val.encode("utf-8")).hexdigest()[:8]
            principal = f"session:{token_hash}"
            request.state.principal = principal
            return principal
        # Backward compatibility check for raw token in test environments
        if cookie_val and hmac.compare_digest(
            cookie_val.encode("utf-8"), settings.forge_access_token.encode("utf-8")
        ):
            token_hash = hashlib.sha256(cookie_val.encode("utf-8")).hexdigest()[:8]
            principal = f"bearer:{token_hash}"
            request.state.principal = principal
            return principal

    raise UnauthorizedError("Authentication required in exposed mode.", details={"mode": "exposed"})
