"""
Runs the full evaluation loop:

    Load eval dataset -> parse each resume once -> run every configured
    model -> score against ground truth -> save JSON + Markdown report.

Model list and dataset path come from configs/models.yaml so adding /
removing / replacing a candidate model never requires touching this script.

Usage:
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --config configs/models.yaml
    python scripts/run_evaluation.py --language en
"""
from __future__ import annotations
from dotenv import load_dotenv
import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(ROOT))

from src.extraction.extractor import get_models, _strip_code_fences  # noqa: E402
from src.evaluation.evaluator import load_eval_dataset, run_evaluation, summarize  # noqa: E402
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "models.yaml"))
    parser.add_argument("--language", choices=("en", "ar"))
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

    details = []
    total_attempts = len(models) * len(eval_items)

    def record_attempt(item, result, extraction):
        detail = {
            "resume_id": item.resume_id,
            "filename": Path(item.resume_path).name,
            "language": item.language,
            "model_name": result.model_name,
            "json_valid": result.json_valid,
            "latency_seconds": result.latency_seconds,
            "f1": result.overall_f1 if result.json_valid else None,
            "error_type": None if result.json_valid else _error_type(result.error, extraction.raw_response),
            "error_message": None if result.json_valid else _redact_secrets(result.error),
        }
        if not result.json_valid and extraction.raw_response:
            detail["raw_response"] = _redact_secrets(extraction.raw_response)
        details.append(detail)

        status = "valid" if result.json_valid else f"INVALID: {detail['error_type']}"
        print(f"[{len(details)}/{total_attempts}] {item.resume_id} - {status}", flush=True)

    results = run_evaluation(models, eval_items, on_attempt=record_attempt)
    summary = summarize(results)

    out_json = str(ROOT / config["report_out_json"])
    out_md = str(ROOT / config["report_out_md"])
    save_json_report(summary, out_json)
    save_markdown_report(summary, out_md)
    out_details = str(Path(out_json).with_name("eval_details.json"))
    Path(out_details).write_text(
        json.dumps(details, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n" + render_markdown_report(summary))
    print(f"\nSaved: {out_json}")
    print(f"Saved: {out_md}")
    print(f"Saved: {out_details}")


if __name__ == "__main__":
    main()
