"""Retry failed evaluation rows without disturbing saved successes."""

import json
import sys

from scripts import run_evaluation as script
from src.evaluation.evaluator import EvalItem
from src.evaluation.metrics import FieldScore, ResumeEvalResult
from src.extraction.extractor import ExtractionResult
from src.extraction.schema import CandidateProfile


def test_retry_failed_replaces_only_selected_model_call_error(tmp_path, monkeypatch):
    config_path = tmp_path / "models.yaml"
    config_path.write_text(
        "models: [served-model, mock]\n"
        "data_dir: data\n"
        "report_out_json: reports/eval_report.json\n"
        "report_out_md: reports/eval_report.md\n",
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    details_path = reports_dir / "eval_details.json"

    def detail(resume_id, language, model, valid, f1, error_type=None):
        return {
            "resume_id": resume_id,
            "filename": f"{resume_id}.pdf",
            "language": language,
            "model_name": model,
            "json_valid": valid,
            "latency_seconds": 10.0,
            "f1": f1,
            "precision": f1 if valid else None,
            "recall": f1 if valid else None,
            "field_scores": ([{
                "field": "full_name", "precision": f1, "recall": f1, "f1": f1,
                "predicted_count": 1, "expected_count": 1, "matched_count": 1,
            }] if valid else []),
            "prompt_tokens": 100 if valid else None,
            "completion_tokens": 20 if valid else None,
            "total_tokens": 120 if valid else None,
            "error_type": error_type,
            "error_message": "previous failure" if error_type else None,
        }

    previous = [
        detail("1-CV", "ar", "served-model", True, 0.5),
        detail("17", "ar", "served-model", False, None, "ModelCallError"),
        detail("7-CV", "ar", "served-model", False, None, "ValidationError"),
        detail("en-cv", "en", "served-model", False, None, "ModelCallError"),
        detail("17", "ar", "mock", True, 0.9),
    ]
    details_path.write_text(json.dumps(previous), encoding="utf-8")
    items = [
        EvalItem(row["resume_id"], str(tmp_path / row["filename"]), row["language"], {})
        for row in previous[:4]
    ]
    calls = []

    def fake_run_evaluation(models, eval_items, on_attempt):
        calls.append((list(models), [(item.language, item.resume_id) for item in eval_items]))
        assert calls[-1] == (["served-model"], [("ar", "17")])
        result = ResumeEvalResult(
            resume_id="17", model_name="served-model", language="ar",
            json_valid=True, latency_seconds=3.0, overall_f1=0.8,
            overall_precision=0.8, overall_recall=0.8,
            field_scores=[FieldScore("full_name", 0.8, 0.8, 0.8, 1, 1, 1)],
            prompt_tokens=11, completion_tokens=4, total_tokens=15,
        )
        extraction = ExtractionResult(
            model_name="test-model", profile=CandidateProfile(), raw_response="{}",
            latency_seconds=3.0, json_valid=True,
        )
        on_attempt(eval_items[0], result, extraction)
        return [result]

    monkeypatch.setattr(script, "ROOT", tmp_path)
    monkeypatch.setattr(script, "load_eval_dataset", lambda _: items)
    monkeypatch.setattr(script, "get_models", lambda _: {"served-model": object(), "mock": object()})
    monkeypatch.setattr(script, "run_evaluation", fake_run_evaluation)
    monkeypatch.setattr(
        sys, "argv",
        ["run_evaluation.py", "--config", str(config_path), "--retry-failed", "--language", "ar"],
    )

    script.main()

    updated = json.loads(details_path.read_text(encoding="utf-8"))
    assert len(calls) == 1
    assert updated[1]["json_valid"] is True
    assert updated[1]["f1"] == 0.8
    assert updated[1]["latency_seconds"] == 3.0
    assert updated[1]["precision"] == 0.8
    assert updated[1]["recall"] == 0.8
    assert updated[1]["field_scores"][0]["field"] == "full_name"
    assert updated[1]["prompt_tokens"] == 11
    for index in (0, 2, 3, 4):
        assert updated[index] == previous[index]

    summary = json.loads((reports_dir / "eval_report.json").read_text(encoding="utf-8"))
    assert summary["served-model"]["n_total"] == 4
    assert summary["served-model"]["json_validity_rate"] == 0.5
    assert summary["served-model"]["avg_f1_overall"] == 0.65
    assert summary["served-model"]["avg_precision_overall"] == 0.65
    assert summary["served-model"]["avg_prompt_tokens"] == 55.5
    assert summary["mock"]["n_total"] == 1
