"""Filesystem path traversal defense and containment verification."""

from pathlib import Path

from mcp_forge.errors import ForgeError


def safe_join(base_dir: Path, untrusted_relative_path: str) -> Path:
    """Safely resolve an untrusted relative path inside base_dir.

    Raises ForgeError with code PATH_TRAVERSAL_DETECTED if traversal is attempted.
    """
    if "\0" in untrusted_relative_path:
        raise ForgeError(
            message="Null bytes in path are prohibited.",
            code="PATH_TRAVERSAL_DETECTED",
            status_code=400,
        )

    # Reject leading slashes, UNC paths, and Windows drive letters
    cleaned = untrusted_relative_path.strip().replace("\\", "/")
    if (
        cleaned.startswith("/")
        or cleaned.startswith("//")
        or (len(cleaned) >= 2 and cleaned[1] == ":")
    ):
        raise ForgeError(
            message="Absolute or drive-rooted paths are prohibited.",
            code="PATH_TRAVERSAL_DETECTED",
            status_code=400,
        )

    base_resolved = base_dir.resolve()
    # Resolve target path relative to base
    target = (base_resolved / cleaned).resolve()

    # Enforce strict containment
    try:
        target.relative_to(base_resolved)
    except ValueError as e:
        raise ForgeError(
            message=f"Path traversal detected for '{untrusted_relative_path}'.",
            code="PATH_TRAVERSAL_DETECTED",
            status_code=400,
        ) from e

    return target
