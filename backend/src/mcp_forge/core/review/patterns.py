"""Regular expression patterns for review rules: instruction injection (SEC-002) and key leaks (SEC-006)."""

import re

# Patterns matching instruction-like text aimed at an AI agent (SEC-002)
INSTRUCTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "ignore_instructions",
        re.compile(
            r"\b(ignore|disregard|override|forget)\s+(all\s+)?(previous|prior|above)?\s*(instructions|prompts|rules|commands)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "hide_from_user",
        re.compile(
            r"\b(do\s+not|never|don't)\s+(tell|reveal|disclose|show|inform)\s+(the\s+)?(user|human|operator)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "exfiltration_intent",
        re.compile(
            r"\b(send|forward|exfiltrate|transmit|upload)\s+(this|the|all)?\s*(data|contents?|secrets?|tokens?|keys?|passwords?)\s+to\b",
            re.IGNORECASE,
        ),
    ),
    (
        "persona_injection",
        re.compile(
            r"\b(you\s+must|you\s+are\s+now|act\s+as)\s+(an?\s+)?(unrestricted|jailbroken|evil|admin|root|system)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "embedded_url",
        re.compile(
            r"https?://[a-zA-Z0-9\-\._~:/\?#\[\]@!$&'\(\)\*\+,;=%]+",
            re.IGNORECASE,
        ),
    ),
]

# Patterns matching key-like or credential-like strings in spec examples (SEC-006)
KEY_LIKE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "openai_key",
        re.compile(r"\bsk-[a-zA-Z0-9_\-]{20,}\b"),
    ),
    (
        "github_token",
        re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{50,})\b"),
    ),
    (
        "aws_access_key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "jwt_token",
        re.compile(r"\beyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b"),
    ),
    (
        "private_key_pem",
        re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
]
