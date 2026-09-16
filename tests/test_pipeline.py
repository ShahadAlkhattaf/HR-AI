import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.language import detect_language, normalize_arabic, clean_text
from src.evaluation.metrics import score_list_string_field, score_scalar_field
from src.models.schema import CandidateProfile


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
        "technical_skills", ["Python", "SQL", "Docker"], ["python", "sql", "Kubernetes"]
    )
    assert score.matched_count == 2
    assert 0 < score.f1 < 1


def test_candidate_profile_schema_roundtrip():
    profile = CandidateProfile(full_name="Test User", technical_skills=["Python"])
    dumped = profile.model_dump()
    reloaded = CandidateProfile.model_validate(dumped)
    assert reloaded.full_name == "Test User"
