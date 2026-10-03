"""Security Test 6 (Unicode & control character part)."""

from mcp_forge.core.security.unicode import clean_unicode_text


def test_invisible_characters_stripped() -> None:
    # Text injected with zero-width spaces, word joiners, and BOM
    hostile_text = "list\u200b_users\u2060_now\ufeff"
    cleaned, has_stripped, count = clean_unicode_text(hostile_text)
    assert cleaned == "list_users_now"
    assert has_stripped is True
    assert count == 3


def test_bidi_override_characters_stripped() -> None:
    # Text injected with Right-to-Left Override (U+202E) and LTR marks
    hostile_text = "dangerous\u202e\u200eoperation"
    cleaned, has_stripped, count = clean_unicode_text(hostile_text)
    assert cleaned == "dangerousoperation"
    assert has_stripped is True
    assert count == 2


def test_control_characters_stripped() -> None:
    # Text injected with null bytes, bell, escape
    hostile_text = "test\x00_endpoint\x07\x1b"
    cleaned, has_stripped, count = clean_unicode_text(hostile_text)
    assert cleaned == "test_endpoint"
    assert has_stripped is True
    assert count == 3


def test_clean_text_unchanged() -> None:
    clean_text = (
        "This is a legitimate description for an API endpoint.\nIncludes newlines and tabs\t."
    )
    cleaned, has_stripped, count = clean_unicode_text(clean_text)
    assert cleaned == clean_text
    assert has_stripped is False
    assert count == 0
