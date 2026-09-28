"""Evaluate configured models on paired resumes and save scores and diagnostics."""
from __future__ import annotations
from dotenv import load_dotenv
import argparse
import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(ROOT))

from src.extraction.extractor import get_models, _strip_code_fences  # noqa: E402
from src.evaluation.evaluator import load_eval_dataset, run_evaluation, summarize  # noqa: E402
from src.evaluation.metrics import FieldScore, ResumeEvalResult  # noqa: E402
from src.evaluation.report import save_json_report, save_markdown_report, render_markdown_report  # noqa: E402


def _error_type(message: str | None, raw_response: str) -> str:
    if not message:
        return "InvalidOutput"
    if message.startswith("model call failed:"):
        return "ModelCallError"
    if message.startswith("JSON parse/validation failed:"):
        try:
            json.loads(_strip_code_fences(raw_response))
        except json.JSONDecodeError:
            return "JSONDecodeError"
        return "ValidationError"
    return "EvaluationError"


def _redact_secrets(value: str | None) -> str | None:
    if value is None:
        return None
    for name, secret in sorted(os.environ.items(), key=lambda pair: len(pair[1]), reverse=True):
        if secret and re.search(r"(?:^|_)(?:API_KEY|TOKEN|SECRET|PASSWORD|ACCESS_KEY)(?:_|$)", name, re.I):
            value = value.replace(secret, "[REDACTED]")
    return re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", value)


def _detail_key(detail: dict) -> tuple[str, str, str]:
    return detail["model_name"], detail["language"], detail["resume_id"]


def _results_from_details(details: list[dict]) -> list[ResumeEvalResult]:
    return [
        ResumeEvalResult(
            resume_id=detail["resume_id"],
            model_name=detail["model_name"],
            language=detail["language"],
            json_valid=detail["json_valid"],
            latency_seconds=detail["latency_seconds"],
            field_scores=[FieldScore(**score) for score in detail["field_scores"]],
            overall_precision=detail["precision"],
            overall_recall=detail["recall"],
            overall_f1=detail["f1"] if detail["json_valid"] else 0.0,
            error=detail.get("error_message"),
            prompt_tokens=detail["prompt_tokens"],
            completion_tokens=detail["completion_tokens"],
            total_tokens=detail["total_tokens"],
        )
        for detail in details
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "models.yaml"))
    parser.add_argument("--language", choices=("en", "ar"))
    parser.add_argument("--retry-failed", action="store_true", help="Retry only previous ModelCallError results")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    data_dir = str(ROOT / config["data_dir"])
    eval_items = load_eval_dataset(data_dir)
    if args.language:
        eval_items = [item for item in eval_items if item.language == args.language]

    if not eval_items:
        print(
            "No eval items found. Run `python scripts/seed_sample_data.py` "
            "first, or add resumes + ground truth under data/."
        )
        sys.exit(1)

    print(f"Loaded {len(eval_items)} eval item(s).")
    print(f"  English: {sum(1 for i in eval_items if i.language == 'en')}")
    print(f"  Arabic:  {sum(1 for i in eval_items if i.language == 'ar')}")

    models = get_models(config["models"])
    print(f"Evaluating models: {list(models.keys())}")

    out_json = str(ROOT / config["report_out_json"])
    out_md = str(ROOT / config["report_out_md"])
    out_details = str(Path(out_json).with_name("eval_details.json"))
    details = []
    retry_by_model = {}
    detail_indexes = {}
    if args.retry_failed:
        details_path = Path(out_details)
        if not details_path.exists():
            parser.error(f"Previous diagnostics not found: {details_path}")
        details = json.loads(details_path.read_text(encoding="utf-8"))
        if not isinstance(details, list):
            parser.error(f"Expected a list of attempts in {details_path}")
        required = {"precision", "recall", "field_scores", "prompt_tokens", "completion_tokens", "total_tokens"}
        if any(not required.issubset(detail) for detail in details):
            parser.error("Previous diagnostics lack benchmark metrics; run a full evaluation once before --retry-failed")
        item_lookup = {(item.language, item.resume_id): item for item in eval_items}
        for index, detail in enumerate(details):
            key = _detail_key(detail)
            if key in detail_indexes:
                parser.error(f"Duplicate previous result for {key}")
            detail_indexes[key] = index
            if detail.get("error_type") != "ModelCallError":
                continue
            if args.language and detail["language"] != args.language:
                continue
            item = item_lookup.get((detail["language"], detail["resume_id"]))
            if item is None or Path(item.resume_path).name != detail["filename"]:
                parser.error(f"Cannot find matching resume for previous result {key}")
            if detail["model_name"] not in models:
                parser.error(f"Model for previous result is not configured: {detail['model_name']}")
            retry_by_model.setdefault(detail["model_name"], []).append(item)
        if not retry_by_model:
            print("No previous ModelCallError results to retry for the selected language.")
            return

    total_attempts = (
        sum(len(items) for items in retry_by_model.values())
        if args.retry_failed else len(models) * len(eval_items)
    )
    attempted = 0

    def record_attempt(item, result, extraction):
        nonlocal attempted
        detail = {
            "resume_id": item.resume_id,
            "filename": Path(item.resume_path).name,
            "language": item.language,
            "model_name": result.model_name,
            "json_valid": result.json_valid,
            "latency_seconds": result.latency_seconds,
            "precision": result.overall_precision if result.json_valid else None,
            "recall": result.overall_recall if result.json_valid else None,
            "f1": result.overall_f1 if result.json_valid else None,
            "field_scores": [asdict(score) for score in result.field_scores],
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
            "error_type": None if result.json_valid else _error_type(result.error, extraction.raw_response),
            "error_message": None if result.json_valid else _redact_secrets(result.error),
        }
        if not result.json_valid and extraction.raw_response:
            detail["raw_response"] = _redact_secrets(extraction.raw_response)
        if args.retry_failed:
            details[detail_indexes[_detail_key(detail)]] = detail
        else:
            details.append(detail)

        attempted += 1
        status = "valid" if result.json_valid else f"INVALID: {detail['error_type']}"
        print(f"[{attempted}/{total_attempts}] {item.resume_id} - {status}", flush=True)

    if args.retry_failed:
        for model_key, items in retry_by_model.items():
            run_evaluation({model_key: models[model_key]}, items, on_attempt=record_attempt)
        results = _results_from_details(details)
    else:
        results = run_evaluation(models, eval_items, on_attempt=record_attempt)
    summary = summarize(results)

    save_json_report(summary, out_json)
    save_markdown_report(summary, out_md)
    Path(out_details).write_text(
        json.dumps(details, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n" + render_markdown_report(summary))
    print(f"\nSaved: {out_json}")
    print(f"Saved: {out_md}")
    print(f"Saved: {out_details}")


if __name__ == "__main__":
    main()
