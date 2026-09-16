"""
Runs stages 1-4 of the pipeline (File Parser -> OCR fallback -> Clean/
normalize) on a single resume and prints the result. Useful for debugging
extraction/OCR issues in isolation, without touching any model.

Usage:
    python scripts/run_pipeline.py path/to/resume.pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.parsing.pipeline import run_parsing_pipeline  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_pipeline.py <resume.pdf|resume.docx>")
        sys.exit(1)

    path = sys.argv[1]
    parsed = run_parsing_pipeline(path)

    print(f"Source:            {parsed.source_path}")
    print(f"File type:         {parsed.file_type}")
    print(f"Extraction method: {parsed.extraction_method}")
    print(f"Detected language: {parsed.detected_language}")
    print(f"Pages:             {parsed.page_count}")
    print(f"Chars (clean):     {parsed.char_count}")
    print("-" * 60)
    print(parsed.clean_text[:2000])
    if len(parsed.clean_text) > 2000:
        print(f"\n... [{len(parsed.clean_text) - 2000} more characters]")


if __name__ == "__main__":
    main()
