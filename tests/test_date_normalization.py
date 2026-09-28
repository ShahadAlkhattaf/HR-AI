"""Date normalization at the CandidateProfile validation boundary."""

import pytest

from src.extraction.schema import CandidateProfile


@pytest.mark.parametrize(
    ("section", "field", "value", "expected"),
    [
        ("education", "start_year", "18/06/2026", "2026-06-18"),
        ("education", "end_year", "21/02/2026", "2026-02-21"),
        ("work_experience", "start_date", "2026/6/18", "2026-06-18"),
        ("work_experience", "start_date", "18.06.2026", "2026-06-18"),
        ("work_experience", "end_date", "06/18/2026", "2026-06-18"),
        ("work_experience", "end_date", "18 June 2026", "2026-06-18"),
        ("certificates", "issue_date", "06/2026", "2026-06"),
        ("certificates", "issue_date", "June 18, 2026", "2026-06-18"),
        ("certificates", "expiry_date", "2026-2", "2026-02"),
        ("education", "start_year", "June 2026", "2026-06"),
        ("education", "end_year", 2026, "2026"),
        ("work_experience", "end_date", "Present", "Present"),
        ("work_experience", "end_date", "حاليًا", "حاليًا"),
        ("certificates", "expiry_date", None, None),
        ("certificates", "issue_date", "31/02/2026", "31/02/2026"),
    ],
)
def test_date_field_normalization(section, field, value, expected):
    profile = CandidateProfile.model_validate({section: [{field: value}]})
    assert getattr(getattr(profile, section)[0], field) == expected


def test_date_normalization_does_not_change_other_fields():
    profile = CandidateProfile.model_validate({
        "education": [{"start_year": "2020", "gpa": 3.75}],
        "work_experience": [{"start_date": "2021", "end_date": None}],
        "certificates": [{"issue_date": "2022", "expiry_date": None}],
    })

    assert profile.education[0].start_year == "2020"
    assert profile.education[0].gpa == "3.75"
    assert profile.work_experience[0].start_date == "2021"
    assert profile.work_experience[0].end_date is None
    assert profile.certificates[0].issue_date == "2022"
    assert profile.certificates[0].expiry_date is None
