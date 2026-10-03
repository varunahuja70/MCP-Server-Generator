"""Response shaping, pretty formatting, truncation, and secret-scrubbed error mapping."""

import json

import httpx

from .logging import redact_secrets


def shape_success_response(response: httpx.Response, max_chars: int = 20000) -> str:
    """Format successful HTTP response body with pretty printing and length truncation."""
    raw_text = response.text

    formatted_text = raw_text
    # Try formatting JSON nicely if content-type is json
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        try:
            parsed = response.json()
            formatted_text = json.dumps(parsed, indent=2)
        except Exception:
            formatted_text = raw_text

    original_length = len(formatted_text)
    if original_length > max_chars:
        excerpt = formatted_text[:max_chars].rstrip()
        return (
            f"{excerpt}\n\n"
            f"[Truncated: response exceeded limit of {max_chars} characters (original length: {original_length} characters)]"
        )

    return formatted_text


def shape_error_response(response: httpx.Response) -> str:
    """Create a safe, secret-scrubbed error message from a non-2xx HTTP response."""
    status_code = response.status_code
    reason = response.reason_phrase or "Error"

    body_snippet = redact_secrets(response.text[:500].strip())

    hint = "Check request parameters and target server status."
    if status_code in (401, 403):
        hint = "Authentication failed or insufficient permissions. Check environment credentials."
    elif status_code == 404:
        hint = "Resource not found. Check the identifier or path parameters."
    elif status_code == 422 or status_code == 400:
        hint = "Invalid request payload or schema mismatch. Verify parameter types."
    elif status_code == 429:
        hint = "Target API rate limit exceeded. Retry after backoff."
    elif status_code >= 500:
        hint = "Target API encountered an internal error. Please check server status."

    msg = f"HTTP {status_code} {reason}\n{hint}"
    if body_snippet:
        msg += f"\nResponse details: {body_snippet}"

    return msg


def shape_exception_error(exc: Exception) -> str:
    """Format a safe, clean error message for network errors without leaking stack traces."""
    if isinstance(exc, httpx.TimeoutException):
        return "Request timed out while waiting for target API response."
    elif isinstance(exc, httpx.ConnectError):
        return (
            "Failed to establish connection to target API. Check network connectivity and base URL."
        )
    elif isinstance(exc, httpx.HTTPError):
        return f"Network or protocol error during request: {redact_secrets(str(exc))}"
    else:
        return f"Unexpected execution error: {redact_secrets(str(exc))}"
