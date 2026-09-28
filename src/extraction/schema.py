"""Candidate profile schema with numeric and date normalization."""
from __future__ import annotations

import calendar
import re
from datetime import date
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


_MONTHS = {
    name.lower(): number
    for number in range(1, 13)
    for name in (calendar.month_name[number], calendar.month_abbr[number])
}


def _normalize_date(value: object) -> object:
    """Normalize recognized dates without filling in missing components."""
    value = _numeric_to_string(value)
    if not isinstance(value, str):
        return value

    text = value.strip()
    year_first = re.fullmatch(r"(\d{4})([./-])(\d{1,2})\2(\d{1,2})", text)
    day_first = re.fullmatch(r"(\d{1,2})([./-])(\d{1,2})\2(\d{4})", text)
    named_day_first = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\.?,?\s+(\d{4})", text)
    named_month_first = re.fullmatch(r"([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})", text)
    if year_first:
        year, month, day = map(int, (year_first[1], year_first[3], year_first[4]))
    elif day_first:
        first, second, year = map(int, (day_first[1], day_first[3], day_first[4]))
        # Prefer day/month/year; use month/day/year only when day-first is impossible.
        day, month = (second, first) if first <= 12 < second else (first, second)
    elif named_day_first and named_day_first[2].lower() in _MONTHS:
        day = int(named_day_first[1])
        month = _MONTHS[named_day_first[2].lower()]
        year = int(named_day_first[3])
    elif named_month_first and named_month_first[1].lower() in _MONTHS:
        month = _MONTHS[named_month_first[1].lower()]
        day = int(named_month_first[2])
        year = int(named_month_first[3])
    else:
        year = month = day = None

    if year is not None:
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return value

    year_month = re.fullmatch(r"(\d{4})[./-](\d{1,2})", text)
    month_year = re.fullmatch(r"(\d{1,2})[./-](\d{4})", text)
    named_month = re.fullmatch(r"([A-Za-z]+)\.?\s+(\d{4})", text)
    if year_month:
        year, month = int(year_month[1]), int(year_month[2])
    elif month_year:
        month, year = int(month_year[1]), int(month_year[2])
    elif named_month and named_month[1].lower() in _MONTHS:
        month, year = _MONTHS[named_month[1].lower()], int(named_month[2])
    else:
        return value

    return f"{year:04d}-{month:02d}" if 1 <= year <= 9999 and 1 <= month <= 12 else value


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    gpa: Optional[str] = None

    @field_validator("start_year", "end_year", mode="before")
    @classmethod
    def normalize_dates(cls, value: object) -> object:
        return _normalize_date(value)

    @field_validator("gpa", mode="before")
    @classmethod
    def normalize_numeric_gpa(cls, value: object) -> object:
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
        return _normalize_date(value)

    model_config = ConfigDict(extra="ignore")


class CertificateEntry(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None

    @field_validator("issue_date", "expiry_date", mode="before")
    @classmethod
    def normalize_numeric_dates(cls, value: object) -> object:
        return _normalize_date(value)

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

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None

    skills: List[str] = Field(default_factory=list)

    certificates: List[CertificateEntry] = Field(default_factory=list)

    projects: List[ProjectEntry] = Field(default_factory=list)

    education: List[EducationEntry] = Field(default_factory=list)

    work_experience: List[WorkExperienceEntry] = Field(default_factory=list)

    # Spoken languages are separate from the detected resume language.
    languages: List[LanguageEntry] = Field(default_factory=list)

    years_of_experience: Optional[float] = None

    # Source-language metadata is not scored.
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
