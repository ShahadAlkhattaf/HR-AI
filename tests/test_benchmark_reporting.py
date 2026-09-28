"""Benchmark summaries reuse the existing deterministic field scores."""

from statistics import mean

from src.evaluation.evaluator import summarize
from src.evaluation.metrics import evaluate_profile
from src.evaluation.report import render_markdown_report
from src.extraction.schema import CandidateProfile


def test_aggregate_quality_validity_latency_and_usage():
    valid = evaluate_profile(
        resume_id="one", model_name="Model A", language="en",
        predicted=CandidateProfile(full_name="Ada", skills=["Python"]),
        expected={"full_name": "Ada", "skills": ["Python", "SQL"]},
        json_valid=True, latency_seconds=2.0,
        prompt_tokens=100, completion_tokens=20, total_tokens=120,
    )
    failed = evaluate_profile(
        resume_id="two", model_name="Model A", language="ar",
        predicted=None, expected={}, json_valid=False, latency_seconds=4.0,
    )
    summary = summarize([valid, failed])["Model A"]

    assert valid.overall_precision == mean(score.precision for score in valid.field_scores)
    assert valid.overall_recall == mean(score.recall for score in valid.field_scores)
    assert valid.overall_f1 == mean(score.f1 for score in valid.field_scores)
    assert summary["json_validity_rate"] == 0.5
    assert summary["avg_latency_seconds_overall"] == 3.0
    assert summary["avg_prompt_tokens"] == 100
    assert summary["avg_completion_tokens"] == 20
    assert summary["avg_total_tokens"] == 120
    assert summary["per_field"]["skills"] == {
        "precision": 1.0, "recall": 0.5, "f1": 0.6667, "n": 1,
    }
    assert summary["english"]["n_total"] == 1
    assert summary["arabic"]["json_validity_rate"] == 0.0

    markdown = render_markdown_report({"Model A": summary})
    assert "Avg Prompt Tokens" in markdown
    assert "Model A: per-field metrics" in markdown
    assert "| Overall | skills | 1.000 | 0.500 | 0.667 | 1 |" in markdown
