"""Deterministic extraction stub for testing without model requests."""
from __future__ import annotations

import json

from .extractor import ResumeExtractionModel
from ..utils.language import detect_language


class MockModel(ResumeExtractionModel):
    def __init__(self, name: str = "mock-model"):
        self.name = name

    def _call(self, prompt: str) -> str:
        # Detect language from resume text rather than prompt instructions.
        resume_text = prompt.split("RESUME TEXT:\n---\n")[-1].split("\n---")[0]
        lang = detect_language(resume_text)
        payload = {
            "full_name": None,
            "email": None,
            "phone": None,
            "location": None,
            "summary": None,
            "github": None,
            "linkedin": None,
            "portfolio": None,
            "skills": [],
            "certificates": [],
            "projects": [],
            "education": [],
            "work_experience": [],
            "languages": [],
            "years_of_experience": None,
            "detected_source_language": lang if lang in ("en", "ar", "mixed") else None,
        }
        return json.dumps(payload, ensure_ascii=False)
