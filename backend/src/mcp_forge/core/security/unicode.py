"""Unicode normalization and defensive stripping of invisible/bidi characters."""

import re
import unicodedata

# Matches invisible characters: zero-width, word joiner, BOM, tag characters, and bidi overrides
# U+200B-U+200D (zero-width spaces/joiners)
# U+200E-U+200F (LTR/RTL marks)
# U+061C (Arabic letter mark)
# U+202A-U+202E (Embedding and override marks)
# U+2060 (Word joiner)
# U+2066-U+2069 (Isolate marks)
# U+FEFF (BOM / zero-width no-break space)
# U+E0000-U+E007F (Tags block)
INVISIBLE_AND_BIDI_PATTERN = re.compile(
    r"[\u200b-\u200f\u061c\u202a-\u202e\u2060\u2066-\u2069\ufeff\U000e0000-\U000e007f]"
)

# Control characters: C0 and C1 controls (excluding tab \t, newline \n, carriage return \r)
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def clean_unicode_text(text: str) -> tuple[str, bool, int]:
    """Normalize text and strip invisible, bidirectional override, and control characters.

    Returns:
        (cleaned_text, has_stripped, stripped_count)
    """
    if not text:
        return text, False, 0

    # 1. Normalize using NFKC to flatten homoglyphs and compatibility characters
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Count and strip invisible and bidi characters
    invisible_matches = len(INVISIBLE_AND_BIDI_PATTERN.findall(normalized))
    cleaned = INVISIBLE_AND_BIDI_PATTERN.sub("", normalized)

    # 3. Count and strip unwanted control characters
    control_matches = len(CONTROL_CHAR_PATTERN.findall(cleaned))
    cleaned = CONTROL_CHAR_PATTERN.sub("", cleaned)

    total_stripped = invisible_matches + control_matches
    has_stripped = total_stripped > 0

    return cleaned, has_stripped, total_stripped
