"""Prompt for extracting a CandidateProfile from resume text."""

from .schema import CandidateProfile


EXTRACTION_SYSTEM_PROMPT = """You are a resume information extraction system.
You will be given the raw text of a resume, which may be in English, Arabic, or a mixture of both.

Extract the candidate's information into ONLY a single JSON object matching this schema exactly:
{schema}

Rules:
- Respond with ONLY the JSON object. No preamble, no markdown fences, no explanation.
- Extract only information that is actually present in the resume text. Never invent, guess, or hallucinate information.
- If a scalar field is not present in the resume, use null. If a list/collection field has no items, use an empty list [].
- Every item in "languages" must be an object with "language" and "proficiency". Never return languages as plain strings. If proficiency is not stated, use null.
- Preserve names and terms in their original language/script (do not translate Arabic names to English or vice versa).
- Set "years_of_experience" only if it is explicitly stated in the resume; otherwise use null.
- Set "detected_source_language" to "en", "ar", or "mixed" based on the resume content.
- This applies equally to English resumes, Arabic resumes, and resumes that mix both languages.
"""


def build_extraction_prompt(resume_text: str) -> str:
    system = EXTRACTION_SYSTEM_PROMPT.format(
        schema=CandidateProfile.json_schema_for_prompt()
    )
    return f"{system}\n\nRESUME TEXT:\n---\n{resume_text}\n---\n\nJSON:"
