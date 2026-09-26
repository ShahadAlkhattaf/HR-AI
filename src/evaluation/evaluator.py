"""
Evaluator: the harness that ties everything together.

    Parsed Resume Text -> Model A/B/C -> Structured JSON -> compare to ground truth -> report

Iterates every (resume, model) pair, calls the common model interface, and
scores against ground truth. English and Arabic resumes are scored
separately as well as combined, per requirement #4.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Callable, Dict, List

from ..extraction.extractor import ExtractionResult, ResumeExtractionModel
from ..parsing.pipeline import run_parsing_pipeline
from .metrics import ResumeEvalResult, evaluate_profile


@dataclass
class EvalItem:
    resume_id: str
    resume_path: str
    language: str  # "en" | "ar"
    ground_truth: dict


def load_eval_dataset(data_dir: str) -> List[EvalItem]:
    """Expects the layout described in the project requirements:

        data/resumes/english/*.pdf|*.docx
        data/resumes/arabic/*.pdf|*.docx
        data/ground_truth/<resume_id>.json
    """
    data_root = Path(data_dir)
    items: List[EvalItem] = []

    for lang, subdir in (("en", "english"), ("ar", "arabic")):
        resume_dir = data_root / "resumes" / subdir
        if not resume_dir.exists():
            continue
        for resume_path in sorted(resume_dir.glob("*")):
            if resume_path.suffix.lower() not in (".pdf", ".docx"):
                continue
            resume_id = resume_path.stem
            gt_path = data_root / "ground_truth" / f"{resume_id}.json"
            if not gt_path.exists():
                # No ground truth yet — skip, but this should be flagged
                # loudly by the caller rather than silently ignored.
                continue
            ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))
            items.append(
                EvalItem(
                    resume_id=resume_id,
                    resume_path=str(resume_path),
                    language=lang,
                    ground_truth=ground_truth,
                )
            )
    return items


def run_evaluation(
    models: Dict[str, ResumeExtractionModel],
    eval_items: List[EvalItem],
    on_attempt: Callable[[EvalItem, ResumeEvalResult, ExtractionResult], None] | None = None,
) -> List[ResumeEvalResult]:
    """Runs every model against every eval item. Parsing happens once per
    resume (not once per model) since the parsing pipeline is model-
    independent — this is the modularity the requirements call for.
    """
    results: List[ResumeEvalResult] = []

    # Parse each resume exactly once, reuse across all models.
    parsed_cache: Dict[str, str] = {}
    for item in eval_items:
        parsed = run_parsing_pipeline(item.resume_path)
        parsed_cache[item.resume_id] = parsed.clean_text

    for model_key, model in models.items():
        for item in eval_items:
            resume_text = parsed_cache[item.resume_id]
            extraction = model.extract(resume_text)
            result = evaluate_profile(
                resume_id=item.resume_id,
                model_name=model_key,
                language=item.language,
                predicted=extraction.profile,
                expected=item.ground_truth,
                json_valid=extraction.json_valid,
                latency_seconds=extraction.latency_seconds,
                error=extraction.error,
            )
            results.append(result)
            if on_attempt is not None:
                on_attempt(item, result, extraction)

    return results


def summarize(results: List[ResumeEvalResult]) -> Dict[str, dict]:
    """Aggregates per-model, and per-model-per-language, summary stats."""
    summary: Dict[str, dict] = {}

    by_model: Dict[str, List[ResumeEvalResult]] = {}
    for r in results:
        by_model.setdefault(r.model_name, []).append(r)

    for model_name, model_results in by_model.items():
        valid = [r for r in model_results if r.json_valid]
        json_validity_rate = len(valid) / len(model_results) if model_results else 0.0

        def lang_stats(lang: str):
            subset = [r for r in valid if r.language == lang]
            if not subset:
                return None
            return {
                "n": len(subset),
                "avg_f1": round(mean(r.overall_f1 for r in subset), 4),
                "avg_latency_seconds": round(mean(r.latency_seconds for r in subset), 3),
            }

        summary[model_name] = {
            "n_total": len(model_results),
            "json_validity_rate": round(json_validity_rate, 4),
            "avg_f1_overall": round(mean(r.overall_f1 for r in valid), 4) if valid else 0.0,
            "avg_latency_seconds_overall": round(mean(r.latency_seconds for r in model_results), 3),
            "english": lang_stats("en"),
            "arabic": lang_stats("ar"),
        }

    return summary
