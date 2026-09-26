"""
Evaluation metrics.

Kept extensible on purpose: quality metrics here now, infrastructure
metrics (latency/VRAM/throughput/cost) added alongside without touching
this module's shape - see evaluation/evaluator.py for how they're combined
into one report row.

All numbers here come from actually running a model against ground truth;
nothing in this file fabricates a result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..extraction.schema import CandidateProfile

# Fields scored as flat strings (simple normalized-string match)
SCALAR_FIELDS = ["full_name", "email", "phone", "years_of_experience"]

# Fields scored as sets of strings (order doesn't matter, near-duplicates ok)
LIST_STRING_FIELDS = ["skills"]

# Fields scored as sets of structured entries (compared on a key sub-field)
LIST_OBJECT_FIELDS = {
    "education": "institution",
    "work_experience": "company",
    "certificates": "name",
    "languages": "language",
}


def _norm(s: Optional[str]) -> str:
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().split())


@dataclass
class FieldScore:
    field: str
    precision: float
    recall: float
    f1: float
    predicted_count: int
    expected_count: int
    matched_count: int


@dataclass
class ResumeEvalResult:
    resume_id: str
    model_name: str
    language: str  # "en" | "ar" | "mixed" — from ground truth metadata
    json_valid: bool
    latency_seconds: float
    field_scores: List[FieldScore] = field(default_factory=list)
    overall_f1: float = 0.0
    error: Optional[str] = None


def _prf1(predicted: set, expected: set) -> tuple[float, float, float, int]:
    matched = len(predicted & expected)
    precision = matched / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = matched / len(expected) if expected else (1.0 if not predicted else 0.0)
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return precision, recall, f1, matched


def score_scalar_field(field_name: str, predicted: Any, expected: Any) -> FieldScore:
    p = {_norm(predicted)} if _norm(predicted) else set()
    e = {_norm(expected)} if _norm(expected) else set()
    precision, recall, f1, matched = _prf1(p, e)
    return FieldScore(field_name, precision, recall, f1, len(p), len(e), matched)


def score_list_string_field(field_name: str, predicted: List[str], expected: List[str]) -> FieldScore:
    p = {_norm(x) for x in (predicted or []) if _norm(x)}
    e = {_norm(x) for x in (expected or []) if _norm(x)}
    precision, recall, f1, matched = _prf1(p, e)
    return FieldScore(field_name, precision, recall, f1, len(p), len(e), matched)


def score_list_object_field(field_name: str, key: str, predicted: List[dict], expected: List[dict]) -> FieldScore:
    def keyset(items):
        out = set()
        for item in items or []:
            val = item.get(key) if isinstance(item, dict) else getattr(item, key, None)
            if _norm(val):
                out.add(_norm(val))
        return out

    p, e = keyset(predicted), keyset(expected)
    precision, recall, f1, matched = _prf1(p, e)
    return FieldScore(field_name, precision, recall, f1, len(p), len(e), matched)


def evaluate_profile(
    resume_id: str,
    model_name: str,
    language: str,
    predicted: Optional[CandidateProfile],
    expected: Dict[str, Any],
    json_valid: bool,
    latency_seconds: float,
    error: Optional[str] = None,
) -> ResumeEvalResult:
    """Compares a model's predicted CandidateProfile against a ground-truth
    dict (loaded from data/ground_truth/*.json) and returns per-field and
    overall scores.
    """
    if not json_valid or predicted is None:
        return ResumeEvalResult(
            resume_id=resume_id,
            model_name=model_name,
            language=language,
            json_valid=False,
            latency_seconds=latency_seconds,
            field_scores=[],
            overall_f1=0.0,
            error=error or "invalid JSON output",
        )

    pred_dict = predicted.model_dump()
    scores: List[FieldScore] = []

    for f_name in SCALAR_FIELDS:
        scores.append(score_scalar_field(f_name, pred_dict.get(f_name), expected.get(f_name)))

    for f_name in LIST_STRING_FIELDS:
        scores.append(score_list_string_field(f_name, pred_dict.get(f_name), expected.get(f_name)))

    for f_name, key in LIST_OBJECT_FIELDS.items():
        scores.append(
            score_list_object_field(f_name, key, pred_dict.get(f_name), expected.get(f_name))
        )

    overall_f1 = sum(s.f1 for s in scores) / len(scores) if scores else 0.0

    return ResumeEvalResult(
        resume_id=resume_id,
        model_name=model_name,
        language=language,
        json_valid=True,
        latency_seconds=latency_seconds,
        field_scores=scores,
        overall_f1=overall_f1,
    )
