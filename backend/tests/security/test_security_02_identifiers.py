"""Security Test 2: Identifier gate and sanitization."""

from mcp_forge.core.security.identifiers import (
    IDENTIFIER_REGEX,
    is_valid_identifier,
    sanitize_identifier,
)


def test_valid_identifiers_pass_gate() -> None:
    valid_names = [
        "list_users",
        "get_pet_by_id",
        "create_item",
        "v1_status",
        "a",
        "a" * 64,
        "calculate_tax_rate_2026",
    ]
    for name in valid_names:
        assert is_valid_identifier(name) is True
        assert IDENTIFIER_REGEX.match(name) is not None


def test_invalid_identifiers_rejected_by_gate() -> None:
    invalid_names = [
        "",
        "123_invalid",
        "_leading_underscore",
        "has-hyphens",
        "has spaces",
        "CamelCaseName",
        "has.dots",
        "has#hash",
        "@has_at",
        "a" * 65,  # Exceeds 64 characters
        'evil"); import os; os.system("rm -rf /")',
        "def",  # Python keyword
        "class",
        "import",
        "server",  # Internal runtime keyword
        "client",
        "mcp",
    ]
    for name in invalid_names:
        assert is_valid_identifier(name) is False


def test_sanitize_identifier_handles_hostile_strings() -> None:
    hostile_inputs = [
        '"); import os; os.system("rm -rf /")',
        "123-bad-name.json!",
        "__multiple___underscores__",
        "UPPERCASE-ACTION",
        "def",  # Keyword
        "server",
        "",
        "   ",
        "a" * 100,
        "日本語_endpoint",
        "<script>alert(1)</script>",
    ]
    for raw in hostile_inputs:
        sanitized = sanitize_identifier(raw, prefix="op")
        # Every sanitized identifier MUST satisfy the strict security gate
        assert is_valid_identifier(sanitized) is True
        assert IDENTIFIER_REGEX.match(sanitized) is not None
        assert len(sanitized) <= 64
