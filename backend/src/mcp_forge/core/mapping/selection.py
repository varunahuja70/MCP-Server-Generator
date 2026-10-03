"""Operation selection logic, safe defaults, presets, and skip determination."""

from typing import Literal

from mcp_forge.core.ir.models import IROperation

PresetName = Literal["read_only", "all", "none"]


def is_read_only_method(method: str) -> bool:
    """Return True if the HTTP method is safe/read-only."""
    return method.upper() in ("GET", "HEAD")


def determine_default_selection(operation: IROperation) -> tuple[bool, bool, str | None]:
    """Determine whether an operation is enabled by default.

    Returns:
        (enabled, skipped, skipped_reason)
    """
    if operation.unsupported_reason:
        return False, True, operation.unsupported_reason

    # Deprecated operations are disabled by default
    if operation.deprecated:
        return False, False, "Operation is marked deprecated in specification"

    # Safe default: only GET and HEAD are enabled by default
    if is_read_only_method(operation.method):
        return True, False, None

    # Write methods (POST, PUT, PATCH, DELETE) are disabled by default
    return False, False, None


def apply_preset(
    operation: IROperation,
    preset: PresetName,
) -> bool:
    """Apply a preset to determine if an operation should be enabled."""
    if operation.unsupported_reason:
        return False

    if preset == "all":
        return True
    elif preset == "read_only":
        return is_read_only_method(operation.method) and not operation.deprecated
    elif preset == "none":
        return False

    return False
