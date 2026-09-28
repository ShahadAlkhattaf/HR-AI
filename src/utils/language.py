"""Detect resume language and normalize Arabic and English text."""
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

# Strip Arabic diacritics while retaining base letters.
_ARABIC_DIACRITICS = re.compile(
    r"[\u064B-\u0652\u0670\u0653-\u065F\u0610-\u061A\u06D6-\u06ED]"
)


def detect_language(text: str) -> str:
    """Classify text as ar, en, mixed, or unknown using Arabic and Latin character ratios."""
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
    """Normalize Unicode, strip Arabic diacritics, unify digits, and normalize alef variants."""
    if not text:
        return text

    text = unicodedata.normalize("NFKC", text)
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.translate(_ARABIC_DIGIT_MAP)

    # Unify alef variants introduced by inconsistent spelling or OCR.
    text = re.sub(r"[إأآا]", "ا", text)
    # Preserve teh marbuta, heh, and alef maksura to avoid changing meaning.
    return text


def clean_text(text: str) -> str:
    """Normalize Unicode and whitespace while preserving line breaks and tabs."""
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    # Retain line breaks and tabs when removing control characters.
    text = "".join(
        ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C"
    )

    # Preserve paragraph boundaries when collapsing excess blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text.strip()
