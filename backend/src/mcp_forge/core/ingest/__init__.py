"""Specification ingestion package."""

from mcp_forge.core.ingest.detect import detect_format
from mcp_forge.core.ingest.limits import (
    DEFAULT_INGEST_TIMEOUT_S,
    DEFAULT_MAX_REDIRECTS,
    DEFAULT_MAX_SPEC_BYTES,
)
from mcp_forge.core.ingest.sources import (
    IngestResult,
    ingest_from_bytes,
    ingest_from_text,
    ingest_from_url,
)

__all__ = [
    "DEFAULT_INGEST_TIMEOUT_S",
    "DEFAULT_MAX_REDIRECTS",
    "DEFAULT_MAX_SPEC_BYTES",
    "IngestResult",
    "detect_format",
    "ingest_from_bytes",
    "ingest_from_text",
    "ingest_from_url",
]
