"""
Common model interface.

    Parsed Resume Text -> [Model A | Model B | Model C] -> CandidateProfile

Every candidate model (commercial frontier, large open-weight, small
open-weight, etc.) implements this same interface. The evaluator and the
parsing pipeline never import a specific model class directly — they depend
only on `ResumeExtractionModel`, so swapping Model A for Model B is a
one-line change (see registry.py).
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .schema import CandidateProfile

EXTRACTION_SYSTEM_PROMPT = """You are a resume information extraction system.
You will be given the raw text of a resume, which may be in English, Arabic, or a mixture of both.

Extract the candidate's information into ONLY a single JSON object matching this schema exactly:
{schema}

Rules:
- Respond with ONLY the JSON object. No preamble, no markdown fences, no explanation.
- If a field is not present in the resume, use null (or an empty list for list fields). Do not invent information.
- Preserve names and terms in their original language/script (do not translate Arabic names to English or vice versa).
- "years_of_experience" should be your best numeric estimate based on work history dates; null if it cannot be determined.
- Set "detected_source_language" to "en", "ar", or "mixed" based on the resume content.
"""


@dataclass
class ExtractionResult:
    """Wraps a model's output with the metadata the evaluator needs
    (latency, raw response, and whether JSON parsing succeeded) so quality
    and infrastructure metrics can both be computed from the same call.
    """

    model_name: str
    profile: Optional[CandidateProfile]
    raw_response: str
    latency_seconds: float
    json_valid: bool
    error: Optional[str] = None


class ResumeExtractionModel(ABC):
    """Base class every candidate model wraps itself in."""

    #: short identifier used in reports/filenames, e.g. "claude-sonnet-4-6"
    name: str = "unnamed-model"

    @abstractmethod
    def _call(self, prompt: str) -> str:
        """Send `prompt` to the underlying model and return the raw text
        response. Subclasses implement only this method.
        """
        raise NotImplementedError

    def build_prompt(self, resume_text: str) -> str:
        system = EXTRACTION_SYSTEM_PROMPT.format(
            schema=CandidateProfile.json_schema_for_prompt()
        )
        return f"{system}\n\nRESUME TEXT:\n---\n{resume_text}\n---\n\nJSON:"

    def extract(self, resume_text: str) -> ExtractionResult:
        """Runs extraction for one resume and returns a structured result.
        This is what the evaluator calls — identical for every model.
        """
        prompt = self.build_prompt(resume_text)

        start = time.perf_counter()
        try:
            raw = self._call(prompt)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ExtractionResult(
                model_name=self.name,
                profile=None,
                raw_response="",
                latency_seconds=elapsed,
                json_valid=False,
                error=f"model call failed: {e}",
            )
        elapsed = time.perf_counter() - start

        cleaned = _strip_code_fences(raw)
        try:
            data = json.loads(cleaned)
            profile = CandidateProfile.model_validate(data)
            return ExtractionResult(
                model_name=self.name,
                profile=profile,
                raw_response=raw,
                latency_seconds=elapsed,
                json_valid=True,
            )
        except Exception as e:
            return ExtractionResult(
                model_name=self.name,
                profile=None,
                raw_response=raw,
                latency_seconds=elapsed,
                json_valid=False,
                error=f"JSON parse/validation failed: {e}",
            )


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()
