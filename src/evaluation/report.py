"""
Turns evaluator output into a saved JSON report and a human-readable
Markdown summary table (English vs Arabic broken out per requirement #4),
ready to paste into the final presentation / Model Card.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def save_json_report(summary: Dict[str, dict], out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def render_markdown_report(summary: Dict[str, dict]) -> str:
    lines = [
        "# Model Evaluation Report",
        "",
        "| Model | N | JSON Validity | Avg F1 (all) | EN F1 | AR F1 | Avg Latency (s) |",
        "|---|---|---|---|---|---|---|",
    ]
    for model_name, s in summary.items():
        en_f1 = f"{s['english']['avg_f1']:.3f}" if s.get("english") else "—"
        ar_f1 = f"{s['arabic']['avg_f1']:.3f}" if s.get("arabic") else "—"
        lines.append(
            f"| {model_name} | {s['n_total']} | {s['json_validity_rate']:.1%} "
            f"| {s['avg_f1_overall']:.3f} | {en_f1} | {ar_f1} | {s['avg_latency_seconds_overall']:.2f} |"
        )
    lines.append("")
    lines.append(
        "_Infrastructure metrics (GPU/VRAM, throughput, cost) are tracked "
        "separately once candidate models are deployed for benchmarking — "
        "see requirement #5 / #6._"
    )
    return "\n".join(lines)


def save_markdown_report(summary: Dict[str, dict], out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(render_markdown_report(summary), encoding="utf-8")
