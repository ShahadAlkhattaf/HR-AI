"""
Runs the full evaluation loop:

    Load eval dataset -> parse each resume once -> run every configured
    model -> score against ground truth -> save JSON + Markdown report.

Model list and dataset path come from configs/models.yaml so adding /
removing / replacing a candidate model never requires touching this script.

Usage:
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --config configs/models.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.registry import get_models  # noqa: E402
from src.evaluation.evaluator import load_eval_dataset, run_evaluation, summarize  # noqa: E402
from src.evaluation.report import save_json_report, save_markdown_report, render_markdown_report  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "models.yaml"))
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    data_dir = str(ROOT / config["data_dir"])
    eval_items = load_eval_dataset(data_dir)

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

    results = run_evaluation(models, eval_items)
    summary = summarize(results)

    out_json = str(ROOT / config["report_out_json"])
    out_md = str(ROOT / config["report_out_md"])
    save_json_report(summary, out_json)
    save_markdown_report(summary, out_md)

    print("\n" + render_markdown_report(summary))
    print(f"\nSaved: {out_json}")
    print(f"Saved: {out_md}")


if __name__ == "__main__":
    main()
