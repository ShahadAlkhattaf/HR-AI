"""
Structured Candidate JSON schema.

This is the single contract every model (Model A, B, C, ...) must produce.
Keeping this schema separate from any model implementation is what lets us
swap models without touching the parsing pipeline or the evaluator.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None


class WorkExperienceEntry(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class CertificationEntry(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[str] = None


class LanguageEntry(BaseModel):
    language: Optional[str] = None
    proficiency: Optional[str] = None  # e.g. native, fluent, intermediate, basic


class CandidateProfile(BaseModel):
    """The structured output every model must produce for a given resume."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    education: List[EducationEntry] = Field(default_factory=list)
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list)
    years_of_experience: Optional[float] = None

    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    languages: List[LanguageEntry] = Field(default_factory=list)

    # metadata useful for bilingual analysis / debugging, not scored directly
    detected_source_language: Optional[str] = None  # "en" | "ar" | "mixed"

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def json_schema_for_prompt(cls) -> str:
        """Compact schema description to embed in model prompts."""
        return (
            '{\n'
            '  "full_name": string|null,\n'
            '  "email": string|null,\n'
            '  "phone": string|null,\n'
            '  "education": [{"degree","field_of_study","institution","start_year","end_year"}],\n'
            '  "work_experience": [{"job_title","company","start_date","end_date","description"}],\n'
            '  "years_of_experience": number|null,\n'
            '  "technical_skills": [string],\n'
            '  "soft_skills": [string],\n'
            '  "certifications": [{"name","issuer","year"}],\n'
            '  "languages": [{"language","proficiency"}],\n'
            '  "detected_source_language": "en"|"ar"|"mixed"|null\n'
            '}'
        )
