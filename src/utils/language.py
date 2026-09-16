"""
Language detection and Arabic/English text normalization helpers.

Kept separate from the parsers so both the file parser and the OCR fallback
can reuse the same logic, and so the model layer never has to guess at
language handling itself.
"""
from __future__ import annotations

import re
import unicodedata

ARABIC_RANGE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
LATIN_RANGE = re.compile(r"[A-Za-z]")

# Arabic-Indic and Eastern Arabic-Indic digits -> ASCII digits
_ARABIC_DIGIT_MAP = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)

# Common Arabic presentation-form ligatures / diacritics to strip for cleaner
# downstream matching (keeps the base letters, removes tashkeel).
_ARABIC_DIACRITICS = re.compile(
    r"[\u064B-\u0652\u0670\u0653-\u065F\u0610-\u061A\u06D6-\u06ED]"
)


def detect_language(text: str) -> str:
    """Return 'ar', 'en', or 'mixed' based on character composition.

    This is a lightweight, dependency-free heuristic used as a fast default.
    For higher-accuracy detection on ambiguous text, swap in `langdetect` or
    `fasttext` behind this same function signature.
    """
    if not text or not text.strip():
        return "unknown"

    arabic_chars = len(ARABIC_RANGE.findall(text))
    latin_chars = len(LATIN_RANGE.findall(text))
    total = arabic_chars + latin_chars

    if total == 0:
        return "unknown"

    arabic_ratio = arabic_chars / total
    if arabic_ratio > 0.85:
        return "ar"
    if arabic_ratio < 0.15:
        return "en"
    return "mixed"


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text: strip diacritics, unify digit forms, unify
    common alef/yeh/teh-marbuta variants so downstream matching is robust.
    """
    if not text:
        return text

    text = unicodedata.normalize("NFKC", text)
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.translate(_ARABIC_DIGIT_MAP)

    # Normalize alef variants to bare alef, common in noisy OCR/extraction
    text = re.sub(r"[إأآا]", "ا", text)
    # Normalize teh marbuta / heh at word end is intentionally NOT done here,
    # since it changes meaning (kept for a future, more careful step).
    # Normalize alef maksura to yeh for matching purposes only downstream.
    return text


def clean_text(text: str) -> str:
    """General cleanup applied to any extracted text (EN, AR, or mixed):
    - collapse excessive whitespace
    - drop control characters
    - normalize unicode
    - fix common ligature/encoding artifacts from PDF extraction
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    # Remove non-printable/control characters except newlines/tabs
    text = "".join(
        ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C"
    )

    # Collapse 3+ blank lines to a max of 2 (preserve structure/paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs (but not newlines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Strip trailing whitespace per line
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text.strip()
