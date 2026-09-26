import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.language import detect_language, normalize_arabic, clean_text
from src.evaluation.metrics import score_list_string_field, score_scalar_field
from src.extraction.schema import CandidateProfile


def test_detect_language_english():
    assert detect_language("Software Engineer with 5 years of experience") == "en"


def test_detect_language_arabic():
    assert detect_language("مهندس برمجيات لديه خمس سنوات من الخبرة") == "ar"


def test_detect_language_mixed():
    text = "مهندس برمجيات - Software Engineer with Python and SQL skills"
    assert detect_language(text) == "mixed"


def test_normalize_arabic_strips_diacritics():
    text = "مُهَنْدِس"
    normalized = normalize_arabic(text)
    assert "\u064E" not in normalized  # fatha removed


def test_clean_text_collapses_whitespace():
    text = "Line one\n\n\n\nLine two   with   spaces"
    cleaned = clean_text(text)
    assert "\n\n\n" not in cleaned
    assert "  " not in cleaned


def test_score_scalar_field_exact_match():
    score = score_scalar_field("email", "a@b.com", "a@b.com")
    assert score.f1 == 1.0


def test_score_scalar_field_mismatch():
    score = score_scalar_field("email", "a@b.com", "c@d.com")
    assert score.f1 == 0.0


def test_score_list_string_field_partial_overlap():
    score = score_list_string_field(
        "skills", ["Python", "SQL", "Docker"], ["python", "sql", "Kubernetes"]
    )
    assert score.matched_count == 2
    assert 0 < score.f1 < 1


def test_candidate_profile_schema_roundtrip():
    profile = CandidateProfile(full_name="Test User", skills=["Python"])
    dumped = profile.model_dump()
    reloaded = CandidateProfile.model_validate(dumped)
    assert reloaded.full_name == "Test User"
    assert reloaded.skills == ["Python"]


def test_candidate_profile_missing_fields_default_safely():
    # Missing scalar fields -> None; missing collections -> [] — never a
    # validation error, per the updated schema requirements.
    profile = CandidateProfile.model_validate({"full_name": "Only Name"})
    assert profile.email is None
    assert profile.location is None
    assert profile.skills == []
    assert profile.certificates == []
    assert profile.projects == []
    assert profile.education == []
    assert profile.work_experience == []


def test_candidate_profile_normalizes_numeric_string_fields():
    profile = CandidateProfile.model_validate({
        "phone": 550081145,
        "education": [{"start_year": 2020, "end_year": 2024.0, "gpa": 4.5}],
        "work_experience": [{"start_date": 2021, "end_date": 2025.0}],
        "certificates": [{"issue_date": 2022, "expiry_date": 2027.0}],
    })

    assert profile.phone == "550081145"
    assert profile.education[0].start_year == "2020"
    assert profile.education[0].end_year == "2024"
    assert profile.education[0].gpa == "4.5"
    assert profile.work_experience[0].start_date == "2021"
    assert profile.work_experience[0].end_date == "2025"
    assert profile.certificates[0].issue_date == "2022"
    assert profile.certificates[0].expiry_date == "2027"


def test_candidate_profile_keeps_structured_languages_strict():
    with pytest.raises(ValidationError):
        CandidateProfile.model_validate({"languages": ["English"]})
