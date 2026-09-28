"""Evaluate model extractions against ground truth and summarize results by language."""
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
    """Pair resumes in data/resumes/english and data/resumes/arabic with ground truth by exact filename stem."""
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
                # Unpaired resumes are omitted from evaluation.
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
    """Parse each resume once and reuse its text across all configured models."""
    results: List[ResumeEvalResult] = []

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
                prompt_tokens=extraction.prompt_tokens,
                completion_tokens=extraction.completion_tokens,
                total_tokens=extraction.total_tokens,
            )
            results.append(result)
            if on_attempt is not None:
                on_attempt(item, result, extraction)

    return results


def summarize(results: List[ResumeEvalResult]) -> Dict[str, dict]:
    summary: Dict[str, dict] = {}

    def average(values):
        known = [value for value in values if value is not None]
        return round(mean(known), 4) if known else None

    def field_averages(valid_results):
        by_field = {}
        for result in valid_results:
            for score in result.field_scores:
                by_field.setdefault(score.field, []).append(score)
        return {
            field: {
                "precision": round(mean(score.precision for score in scores), 4),
                "recall": round(mean(score.recall for score in scores), 4),
                "f1": round(mean(score.f1 for score in scores), 4),
                "n": len(scores),
            }
            for field, scores in by_field.items()
        }

    def usage_averages(attempts):
        return {
            f"avg_{field}": average(getattr(result, field) for result in attempts)
            for field in ("prompt_tokens", "completion_tokens", "total_tokens")
        }

    by_model: Dict[str, List[ResumeEvalResult]] = {}
    for r in results:
        by_model.setdefault(r.model_name, []).append(r)

    for model_name, model_results in by_model.items():
        valid = [r for r in model_results if r.json_valid]
        json_validity_rate = len(valid) / len(model_results) if model_results else 0.0

        def lang_stats(lang: str):
            attempts = [r for r in model_results if r.language == lang]
            if not attempts:
                return None
            subset = [r for r in attempts if r.json_valid]
            return {
                "n": len(subset),
                "n_total": len(attempts),
                "json_validity_rate": round(len(subset) / len(attempts), 4),
                "avg_precision": average(r.overall_precision for r in subset),
                "avg_recall": average(r.overall_recall for r in subset),
                "avg_f1": round(mean(r.overall_f1 for r in subset), 4) if subset else 0.0,
                "per_field": field_averages(subset),
                "avg_latency_seconds": round(mean(r.latency_seconds for r in subset), 3) if subset else None,
                "avg_latency_seconds_all": round(mean(r.latency_seconds for r in attempts), 3),
                **usage_averages(attempts),
            }

        summary[model_name] = {
            "n_total": len(model_results),
            "json_validity_rate": round(json_validity_rate, 4),
            "avg_precision_overall": average(r.overall_precision for r in valid),
            "avg_recall_overall": average(r.overall_recall for r in valid),
            "avg_f1_overall": round(mean(r.overall_f1 for r in valid), 4) if valid else 0.0,
            "per_field": field_averages(valid),
            "avg_latency_seconds_overall": round(mean(r.latency_seconds for r in model_results), 3),
            **usage_averages(model_results),
            "english": lang_stats("en"),
            "arabic": lang_stats("ar"),
        }

    return summary
