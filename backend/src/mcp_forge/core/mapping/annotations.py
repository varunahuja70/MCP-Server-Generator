"""Map operation HTTP method to MCP ToolAnnotations."""

from typing import Any


def get_tool_annotations(method: str, title: str | None = None) -> dict[str, Any]:
    """Derive MCP tool annotations from HTTP method and title.

    Matches specification:
    - GET / HEAD: read-only, idempotent
    - DELETE: destructive, idempotent
    - PUT: idempotent write
    - POST / PATCH: non-idempotent write
    All operations are open-world (reach external systems).
    """
    m = method.upper()

    read_only = m in ("GET", "HEAD")
    destructive = m == "DELETE"
    idempotent = m in ("GET", "HEAD", "PUT", "DELETE")
    open_world = True

    annotations: dict[str, Any] = {
        "read_only_hint": read_only,
        "destructive_hint": destructive,
        "idempotent_hint": idempotent,
        "open_world_hint": open_world,
    }

    if title:
        annotations["title"] = title

    return annotations
