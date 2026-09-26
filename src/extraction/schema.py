"""
Structured Candidate JSON schema.

This is the single contract every model (Model A, B, C, ...) must produce.
Keeping this schema separate from any model implementation is what lets us
swap models without touching the parsing pipeline or the evaluator.

Shape is designed to approximate the target HR AI application's demo
sections (Profile / Certificates / Skills / Projects / Education /
Experience) while we wait for the real API contract. Field names may need
to be renamed once that contract is available, but the section boundaries
below (Education, WorkExperience, Certificate, Project) are kept as
separate models specifically so that remapping later is a matter of
renaming fields, not restructuring data.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _numeric_to_string(value: object) -> object:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    return value


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    gpa: Optional[str] = None

    @field_validator("start_year", "end_year", "gpa", mode="before")
    @classmethod
    def normalize_numeric_fields(cls, value: object) -> object:
        return _numeric_to_string(value)

    model_config = ConfigDict(extra="ignore")


class WorkExperienceEntry(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def normalize_numeric_dates(cls, value: object) -> object:
        return _numeric_to_string(value)

    model_config = ConfigDict(extra="ignore")


class CertificateEntry(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None

    @field_validator("issue_date", "expiry_date", mode="before")
    @classmethod
    def normalize_numeric_dates(cls, value: object) -> object:
        return _numeric_to_string(value)

    model_config = ConfigDict(extra="ignore")


class ProjectEntry(BaseModel):
    name: Optional[str] = None
    link: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class LanguageEntry(BaseModel):
    language: Optional[str] = None
    proficiency: Optional[str] = None  # e.g. native, fluent, intermediate, basic

    model_config = ConfigDict(extra="ignore")


class CandidateProfile(BaseModel):
    """The structured output every model must produce for a given resume.

    Field groups map onto the target demo's display sections:
      Profile:      full_name, email, phone, location, summary, github,
                     linkedin, portfolio
      Certificates: certificates
      Skills:       skills
      Projects:     projects
      Education:    education
      Experience:   work_experience
    """

    # --- Profile ---
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None

    # --- Skills (single flat list, matches the demo) ---
    skills: List[str] = Field(default_factory=list)

    # --- Certificates ---
    certificates: List[CertificateEntry] = Field(default_factory=list)

    # --- Projects ---
    projects: List[ProjectEntry] = Field(default_factory=list)

    # --- Education ---
    education: List[EducationEntry] = Field(default_factory=list)

    # --- Experience ---
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list)

    # --- Languages spoken (not the same as detected_source_language below) ---
    languages: List[LanguageEntry] = Field(default_factory=list)

    years_of_experience: Optional[float] = None

    # metadata useful for bilingual analysis / debugging, not scored directly
    detected_source_language: Optional[str] = None  # "en" | "ar" | "mixed"

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_numeric_phone(cls, value: object) -> object:
        return _numeric_to_string(value)

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def json_schema_for_prompt(cls) -> str:
        """Compact schema description to embed in model prompts."""
        return (
            '{\n'
            '  "full_name": string|null,\n'
            '  "email": string|null,\n'
            '  "phone": string|null,\n'
            '  "location": string|null,\n'
            '  "summary": string|null,\n'
            '  "github": string|null,\n'
            '  "linkedin": string|null,\n'
            '  "portfolio": string|null,\n'
            '  "skills": [string],\n'
            '  "certificates": [{"name","issuer","issue_date","expiry_date"}],\n'
            '  "projects": [{"name","link","description"}],\n'
            '  "education": [{"degree","institution","start_year","end_year","gpa"}],\n'
            '  "work_experience": [{"company","role","start_date","end_date","description"}],\n'
            '  "languages": [{"language","proficiency"}],\n'
            '  "years_of_experience": number|null,\n'
            '  "detected_source_language": "en"|"ar"|"mixed"|null\n'
            '}'
        )
