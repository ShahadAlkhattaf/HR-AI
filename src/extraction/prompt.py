"""Prompt for extracting a CandidateProfile from resume text."""

from .schema import CandidateProfile


EXTRACTION_SYSTEM_PROMPT = """You extract structured information from English, Arabic, or mixed-language resumes.

Return ONLY one valid JSON object matching this schema:
{schema}

Rules:
- Extract only information supported by the resume; do not invent or guess.
- Use null for missing values (never placeholder text) and [] for missing lists.
- Return languages as {{"language": ..., "proficiency": ...}}; use null for missing proficiency.
- Preserve names and terms in their original language/script.
- For "years_of_experience", use the stated total or calculate it from available work dates without guessing missing dates; otherwise use null.
- Set "detected_source_language" to "en", "ar", or "mixed".
- Return only valid JSON with no markdown or explanation. Keep formatted values such as GPA ("4.16/5") as strings.
"""


def build_extraction_prompt(resume_text: str) -> str:
    system = EXTRACTION_SYSTEM_PROMPT.format(
        schema=CandidateProfile.json_schema_for_prompt()
    )
    return f"{system}\n\nRESUME TEXT:\n---\n{resume_text}\n---\n\nJSON:"
