"""
Mock model: no API calls, deterministic output.

Used to smoke-test the pipeline (parsing -> model interface -> evaluator ->
metrics) end-to-end before spending money on real model calls, and useful
in CI. Not a "candidate" model for the real evaluation.
"""
from __future__ import annotations

import json

from .extractor import ResumeExtractionModel
from ..utils.language import detect_language


class MockModel(ResumeExtractionModel):
    def __init__(self, name: str = "mock-model"):
        self.name = name

    def _call(self, prompt: str) -> str:
        # Pull the resume text back out of the prompt just for the demo,
        # and return a syntactically-valid but low-effort profile so the
        # evaluator machinery can be exercised without any real inference.
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
