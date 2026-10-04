import asyncio
import json
import time
from typing import Any

from mcp_forge.core.security.redact import redact_text

MAX_TRACE_MESSAGE_CHARS = 100_000
MAX_SESSION_TRACE_EVENTS = 1_000


class TraceRecorder:
    """Records protocol trace messages with timestamps, direction, size limits, and secret redaction."""

    def __init__(self, session_id: str, extra_secrets: set[str] | None = None) -> None:
        self.session_id = session_id
        self.extra_secrets = extra_secrets or set()
        self.events: list[dict[str, Any]] = []
        self._seq = 0
        self._subscribers: list[asyncio.Queue[dict[str, Any]]] = []

    def record(
        self,
        direction: str,  # client_to_server, server_to_client, stderr
        message: Any,
        duration_ms: float | None = None,
    ) -> dict[str, Any]:
        """Record and redact a trace message."""
        self._seq += 1

        if isinstance(message, (dict, list)):
            raw_text = json.dumps(message)
        else:
            raw_text = str(message)

        # Truncate if message exceeds maximum length
        if len(raw_text) > MAX_TRACE_MESSAGE_CHARS:
            raw_text = raw_text[:MAX_TRACE_MESSAGE_CHARS] + "... [TRUNCATED]"

        # Redact credentials and secret patterns
        safe_message = redact_text(raw_text, extra_secrets=self.extra_secrets)

        event = {
            "session_id": self.session_id,
            "seq": self._seq,
            "direction": direction,
            "message_json": safe_message,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
        }

        # Keep events list bounded
        if len(self.events) >= MAX_SESSION_TRACE_EVENTS:
            self.events.pop(0)
        self.events.append(event)

        # Notify any active SSE subscribers
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except Exception:  # noqa: S110
                pass

        return event

    def subscribe(self) -> "asyncio.Queue[dict[str, Any]]":
        """Subscribe to real-time events for SSE stream."""
        import asyncio

        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: "asyncio.Queue[dict[str, Any]]") -> None:
        """Unsubscribe from real-time events."""
        if q in self._subscribers:
            self._subscribers.remove(q)
