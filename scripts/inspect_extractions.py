"""Save parsed text, ground truth, and extraction output for inspection."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

from src.evaluation.evaluator import load_eval_dataset  # noqa: E402
from src.extraction.extractor import get_model  # noqa: E402
from src.parsing.pipeline import run_parsing_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("en", "ar"), required=True)
    parser.add_argument("--config", default=str(ROOT / "configs" / "models.yaml"))
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    data_dir = ROOT / config["data_dir"]
    items = [
        item for item in load_eval_dataset(str(data_dir))
        if item.language == args.language
    ]

    subdir = "english" if args.language == "en" else "arabic"
    resume_dir = data_dir / "resumes" / subdir
    resume_files = sorted(
        path for path in resume_dir.glob("*")
        if path.suffix.lower() in (".pdf", ".docx")
    )
    paired_paths = {Path(item.resume_path) for item in items}
    missing = [path.name for path in resume_files if path not in paired_paths]
    if missing:
        parser.error("Missing ground truth for: " + ", ".join(missing))
    if not items:
        parser.error(f"No paired {args.language} resumes found in {resume_dir}")

    model = get_model("served-model")
    output_dir = ROOT / "reports" / "inspection" / args.language
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, item in enumerate(items, 1):
        output = {
            "resume_id": item.resume_id,
            "parsed_text": None,
            "ground_truth": item.ground_truth,
            "model_output": None,
            "raw_response": "",
            "json_valid": False,
            "error": None,
        }
        try:
            parsed = run_parsing_pipeline(item.resume_path)
        except Exception as exc:
            output["error"] = f"Parsing failed: {type(exc).__name__}: {exc}"
        else:
            output["parsed_text"] = parsed.clean_text
            try:
                extraction = model.extract(parsed.clean_text)
            except Exception as exc:
                output["error"] = f"Extraction failed: {type(exc).__name__}: {exc}"
            else:
                output["model_output"] = (
                    extraction.profile.model_dump()
                    if extraction.json_valid and extraction.profile is not None
                    else None
                )
                output["raw_response"] = extraction.raw_response
                output["json_valid"] = extraction.json_valid
                output["error"] = extraction.error

        output_path = output_dir / f"{item.resume_id}.json"
        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        status = "valid" if output["json_valid"] else "INVALID"
        print(f"[{index}/{len(items)}] {item.resume_id} - {status}: {output_path}")


if __name__ == "__main__":
    main()
