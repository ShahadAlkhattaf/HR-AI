"""
Parsing pipeline orchestrator.

    Resume -> File Parser -> OCR fallback (if needed) -> Clean/normalize -> ParsedResume

This is the ONLY module the model layer / evaluator should depend on for
getting resume text. It deliberately knows nothing about which LLM will
consume its output, so parser/OCR improvements never require touching
model code, and models can be swapped without touching parsing code.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .file_parser import parse_file, ParseResult
from .ocr import apply_ocr_fallback, OcrConfig
from ..utils.language import detect_language, normalize_arabic, clean_text


@dataclass
class ParsedResume:
    source_path: str
    file_type: str
    extraction_method: str  # "native" | "ocr"
    raw_text: str
    clean_text: str
    detected_language: str  # "en" | "ar" | "mixed" | "unknown"
    page_count: int
    char_count: int


def run_parsing_pipeline(path: str, ocr_config: OcrConfig | None = None) -> ParsedResume:
    """Runs the full modular pipeline for a single resume file and returns
    normalized text + metadata ready to be handed to any model.
    """
    result: ParseResult = parse_file(path)

    if result.needs_ocr:
        result = apply_ocr_fallback(result, ocr_config or OcrConfig())

    raw_text = result.full_text
    language = detect_language(raw_text)

    normalized = raw_text
    if language in ("ar", "mixed"):
        normalized = normalize_arabic(normalized)
    normalized = clean_text(normalized)

    return ParsedResume(
        source_path=str(Path(path)),
        file_type=result.file_type,
        extraction_method=result.extraction_method,
        raw_text=raw_text,
        clean_text=normalized,
        detected_language=language,
        page_count=len(result.pages),
        char_count=len(normalized),
    )
