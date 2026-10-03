"""Specification ingestion from file uploads, raw text paste, links, and samples."""

import hashlib
from dataclasses import dataclass
from typing import Literal

from mcp_forge.core.ingest.detect import detect_format
from mcp_forge.core.ingest.limits import (
    DEFAULT_INGEST_TIMEOUT_S,
    DEFAULT_MAX_REDIRECTS,
    DEFAULT_MAX_SPEC_BYTES,
)
from mcp_forge.core.security.ssrf import safe_fetch_url
from mcp_forge.core.security.unicode import clean_unicode_text
from mcp_forge.errors import InvalidSpecError

ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/yaml",
    "application/x-yaml",
    "text/yaml",
    "text/x-yaml",
    "text/plain",
    "application/octet-stream",
}


@dataclass(frozen=True)
class IngestResult:
    """Standardized metadata result of an ingested specification."""

    raw_text: str
    format: Literal["json", "yaml"]
    sha256: str
    byte_count: int
    source_type: Literal["file", "paste", "url", "sample"]
    source_ref: str
    has_stripped_chars: bool = False
    stripped_char_count: int = 0


def ingest_from_text(
    text: str,
    source_type: Literal["paste", "sample"] = "paste",
    source_ref: str = "pasted-spec",
    max_bytes: int = DEFAULT_MAX_SPEC_BYTES,
) -> IngestResult:
    """Ingest specification from raw text."""
    if not text or not text.strip():
        raise InvalidSpecError("Specification text cannot be empty.")

    raw_bytes = text.encode("utf-8")
    if len(raw_bytes) > max_bytes:
        raise InvalidSpecError(
            f"Specification size ({len(raw_bytes)} bytes) exceeds maximum limit of {max_bytes} bytes.",
            details={"byte_count": len(raw_bytes), "max_bytes": max_bytes},
        )

    cleaned_text, has_stripped, stripped_count = clean_unicode_text(text)
    spec_format = detect_format(cleaned_text)
    sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

    return IngestResult(
        raw_text=cleaned_text,
        format=spec_format,
        sha256=sha256_hash,
        byte_count=len(raw_bytes),
        source_type=source_type,
        source_ref=source_ref,
        has_stripped_chars=has_stripped,
        stripped_char_count=stripped_count,
    )


def ingest_from_bytes(
    data: bytes,
    source_type: Literal["file", "sample", "url"] = "file",
    source_ref: str = "upload.yaml",
    max_bytes: int = DEFAULT_MAX_SPEC_BYTES,
) -> IngestResult:
    """Ingest specification from uploaded raw bytes."""
    if not data:
        raise InvalidSpecError("Uploaded specification file is empty.")

    if len(data) > max_bytes:
        raise InvalidSpecError(
            f"Uploaded file size ({len(data)} bytes) exceeds maximum limit of {max_bytes} bytes.",
            details={"byte_count": len(data), "max_bytes": max_bytes},
        )

    try:
        text = data.decode("utf-8-sig")  # Handles BOM automatically
    except UnicodeDecodeError as e:
        raise InvalidSpecError(
            f"File encoding error: specification must be UTF-8 encoded ({e})."
        ) from e

    cleaned_text, has_stripped, stripped_count = clean_unicode_text(text)
    spec_format = detect_format(cleaned_text)
    sha256_hash = hashlib.sha256(data).hexdigest()

    return IngestResult(
        raw_text=cleaned_text,
        format=spec_format,
        sha256=sha256_hash,
        byte_count=len(data),
        source_type=source_type,
        source_ref=source_ref,
        has_stripped_chars=has_stripped,
        stripped_char_count=stripped_count,
    )


async def ingest_from_url(
    url: str,
    allow_private: bool = False,
    max_bytes: int = DEFAULT_MAX_SPEC_BYTES,
    timeout_s: float = DEFAULT_INGEST_TIMEOUT_S,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
) -> IngestResult:
    """Fetch and ingest specification from an HTTP(S) URL with SSRF protection."""
    content_bytes, content_type = await safe_fetch_url(
        url=url,
        max_redirects=max_redirects,
        allow_private=allow_private,
        timeout_s=timeout_s,
        max_bytes=max_bytes,
    )

    # Validate content-type header
    mime_base = content_type.split(";")[0].strip().lower()
    if mime_base and mime_base not in ALLOWED_CONTENT_TYPES:
        raise InvalidSpecError(
            f"Invalid Content-Type '{content_type}'. Expected JSON or YAML specification.",
            details={"content_type": content_type},
        )

    return ingest_from_bytes(
        data=content_bytes,
        source_type="url",
        source_ref=url,
        max_bytes=max_bytes,
    )
