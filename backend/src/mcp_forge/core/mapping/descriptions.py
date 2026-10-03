"""Tool and parameter description cleaning, markdown flattening, and length capping."""

import re

from mcp_forge.core.security.unicode import clean_unicode_text


def flatten_markdown(text: str) -> str:
    """Convert markdown formatting into plain readable text."""
    if not text:
        return ""

    # Replace markdown links: [text](url) -> text
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove HTML tags: <tag> -> ""
    s = re.sub(r"<[^>]+>", "", s)
    # Remove markdown headers: # header -> header
    s = re.sub(r"^#+\s*", "", s, flags=re.MULTILINE)
    # Remove bold/italic markers (* or _)
    s = re.sub(r"[*_]{1,3}", "", s)
    # Remove inline code backticks
    s = re.sub(r"`([^`]+)`", r"\1", s)
    # Remove code blocks
    s = re.sub(r"```[a-zA-Z0-9_-]*\n([\s\S]*?)\n```", r"\1", s)
    # Collapse multiple whitespaces and newlines
    s = re.sub(r"\r\n|\r|\n", " ", s)
    s = re.sub(r"\s+", " ", s)

    return s.strip()


def clean_description(text: str | None, max_length: int = 1000) -> str:
    """Clean invisible characters, flatten markdown, and cap description length."""
    if not text:
        return ""

    cleaned, _, _ = clean_unicode_text(text)
    plain = flatten_markdown(cleaned)

    if len(plain) > max_length:
        plain = plain[:max_length].rstrip() + "..."

    return plain


def build_tool_description(
    summary: str | None = None,
    description: str | None = None,
    parameter_notes: list[str] | None = None,
    max_length: int = 1000,
) -> str:
    """Combine summary, description, and optional parameter notes into a clean tool description."""
    parts: list[str] = []

    clean_summary = clean_description(summary, max_length=300)
    clean_desc = clean_description(description, max_length=700)

    if clean_summary:
        parts.append(clean_summary)

    # Avoid duplicating summary if description starts with it
    if clean_desc and clean_desc != clean_summary:
        if clean_summary and clean_desc.startswith(clean_summary):
            clean_desc = clean_desc[len(clean_summary) :].strip()
        if clean_desc:
            parts.append(clean_desc)

    if parameter_notes:
        notes_str = "; ".join(clean_description(n, max_length=150) for n in parameter_notes if n)
        if notes_str:
            parts.append(f"Parameters: {notes_str}")

    combined = " - ".join(p for p in parts if p)
    if not combined:
        return "No description provided."

    if len(combined) > max_length:
        combined = combined[:max_length].rstrip() + "..."

    return combined
