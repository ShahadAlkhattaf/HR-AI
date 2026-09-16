"""
Stage 2: OCR fallback.

Only invoked when file_parser.ParseResult.needs_ocr is True (e.g. scanned
resume, image-only PDF page, or a font-encoding issue that corrupted native
Arabic extraction). Uses Tesseract with both Arabic and English language
packs loaded simultaneously ("ara+eng") so mixed-language resumes and
bilingual headers/sections are OCR'd correctly in one pass.

Requires system packages: tesseract-ocr, tesseract-ocr-ara, poppler-utils
(for pdf2image). See README for setup / Dockerfile snippet.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .file_parser import ParseResult, ParsedPage

# Tesseract language codes: Arabic + English loaded together.
OCR_LANGS = "ara+eng"


@dataclass
class OcrConfig:
    langs: str = OCR_LANGS
    dpi: int = 300  # higher DPI materially improves Arabic OCR accuracy
    psm: int = 3  # automatic page segmentation


def _ocr_image(image, config: OcrConfig) -> str:
    import pytesseract

    tess_config = f"--psm {config.psm}"
    return pytesseract.image_to_string(image, lang=config.langs, config=tess_config)


def ocr_pdf(path: str, config: OcrConfig = OcrConfig()) -> List[ParsedPage]:
    from pdf2image import convert_from_path

    images = convert_from_path(path, dpi=config.dpi)
    pages: List[ParsedPage] = []
    for i, image in enumerate(images):
        text = _ocr_image(image, config)
        pages.append(ParsedPage(page_number=i + 1, text=text))
    return pages


def ocr_docx_images(path: str, config: OcrConfig = OcrConfig()) -> List[ParsedPage]:
    """Best-effort OCR of any images embedded in a DOCX (e.g. a resume that
    is actually a screenshot pasted into Word). Rare, but included for
    pipeline completeness.
    """
    import zipfile
    import io
    from PIL import Image

    pages: List[ParsedPage] = []
    with zipfile.ZipFile(path) as z:
        media_files = [n for n in z.namelist() if n.startswith("word/media/")]
        for i, name in enumerate(sorted(media_files)):
            try:
                image = Image.open(io.BytesIO(z.read(name)))
                text = _ocr_image(image, config)
                pages.append(ParsedPage(page_number=i + 1, text=text))
            except Exception:
                continue
    return pages


def apply_ocr_fallback(result: ParseResult, config: OcrConfig = OcrConfig()) -> ParseResult:
    """Re-runs OCR for any page whose native extraction was insufficient,
    and merges the OCR text in, preserving pages that already extracted
    cleanly. Returns a new ParseResult with extraction_method='ocr' for any
    modified page set.
    """
    if not result.needs_ocr:
        return result

    if result.file_type == "pdf":
        ocr_pages = ocr_pdf(result.source_path, config)
    elif result.file_type == "docx":
        ocr_pages = ocr_docx_images(result.source_path, config)
    else:
        return result

    # Merge: prefer native text per-page if it was already above threshold,
    # otherwise use the OCR'd text for that page index.
    from .file_parser import MIN_CHARS_PER_PAGE_THRESHOLD

    merged: List[ParsedPage] = []
    native_by_index = {p.page_number: p for p in result.pages}
    max_pages = max(len(result.pages), len(ocr_pages)) if ocr_pages else len(result.pages)

    for i in range(1, max_pages + 1):
        native = native_by_index.get(i)
        if native and native.char_count >= MIN_CHARS_PER_PAGE_THRESHOLD:
            merged.append(native)
        else:
            ocr_page = next((p for p in ocr_pages if p.page_number == i), None)
            merged.append(ocr_page if ocr_page else (native or ParsedPage(i, "")))

    return ParseResult(
        source_path=result.source_path,
        file_type=result.file_type,
        pages=merged,
        extraction_method="ocr",
        needs_ocr=False,
    )
