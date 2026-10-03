"""Error models and exceptions for MCP Forge."""

from typing import Any


class ForgeError(Exception):
    """Base exception for all MCP Forge errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class UnsafeConfigError(ForgeError):
    """Raised when application configuration violates security constraints."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            code="UNSAFE_CONFIG",
            status_code=500,
            details=details,
        )


class InvalidSpecError(ForgeError):
    """Raised when an OpenAPI/Swagger spec is invalid."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            code="SPEC_INVALID",
            status_code=400,
            details=details,
        )


class NotFoundError(ForgeError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConflictError(ForgeError):
    """Raised when a resource state conflict occurs."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class UnauthorizedError(ForgeError):
    """Raised when authentication is missing or invalid."""

    def __init__(self, message: str = "Authentication required", details: Any = None) -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details,
        )


class ForbiddenError(ForgeError):
    """Raised when access is forbidden."""

    def __init__(self, message: str = "Access forbidden", details: Any = None) -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class RateLimitError(ForgeError):
    """Raised when a rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Any = None) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class SSRFBlockedError(ForgeError):
    """Raised when a target address is blocked by SSRF protection."""

    def __init__(self, message: str = "SSRF target address blocked", details: Any = None) -> None:
        super().__init__(
            message=message,
            code="SSRF_BLOCKED",
            status_code=400,
            details=details,
        )
