"""Save aggregate evaluation metrics as JSON and Markdown reports."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def save_json_report(summary: Dict[str, dict], out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def render_markdown_report(summary: Dict[str, dict]) -> str:
    def fmt(value, decimals=3):
        return f"{value:.{decimals}f}" if value is not None else "—"

    lines = [
        "# Model Evaluation Report",
        "",
        "| Model | N | JSON Validity | Precision | Recall | F1 | EN F1 | AR F1 | Avg Latency (s) | Avg Prompt Tokens | Avg Completion Tokens | Avg Total Tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model_name, s in summary.items():
        en_f1 = fmt(s["english"]["avg_f1"]) if s.get("english") else "—"
        ar_f1 = fmt(s["arabic"]["avg_f1"]) if s.get("arabic") else "—"
        lines.append(
            f"| {model_name} | {s['n_total']} | {s['json_validity_rate']:.1%} "
            f"| {fmt(s['avg_precision_overall'])} | {fmt(s['avg_recall_overall'])} "
            f"| {fmt(s['avg_f1_overall'])} | {en_f1} | {ar_f1} "
            f"| {fmt(s['avg_latency_seconds_overall'], 2)} "
            f"| {fmt(s['avg_prompt_tokens'], 1)} | {fmt(s['avg_completion_tokens'], 1)} "
            f"| {fmt(s['avg_total_tokens'], 1)} |"
        )
    for model_name, model_stats in summary.items():
        lines.extend([
            "",
            f"## {model_name}: language metrics",
            "",
            "| Language | N | JSON Validity | Precision | Recall | F1 | Avg Latency (s) | Avg Prompt Tokens | Avg Completion Tokens | Avg Total Tokens |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for language, stats in (("English", model_stats.get("english")), ("Arabic", model_stats.get("arabic"))):
            if stats is None:
                continue
            lines.append(
                f"| {language} | {stats['n_total']} | {stats['json_validity_rate']:.1%} "
                f"| {fmt(stats['avg_precision'])} | {fmt(stats['avg_recall'])} | {fmt(stats['avg_f1'])} "
                f"| {fmt(stats['avg_latency_seconds_all'], 2)} "
                f"| {fmt(stats['avg_prompt_tokens'], 1)} | {fmt(stats['avg_completion_tokens'], 1)} "
                f"| {fmt(stats['avg_total_tokens'], 1)} |"
            )
        lines.extend([
            "",
            f"## {model_name}: per-field metrics",
            "",
            "| Scope | Field | Precision | Recall | F1 | N |",
            "|---|---|---:|---:|---:|---:|",
        ])
        for scope, stats in (
            ("Overall", model_stats),
            ("English", model_stats.get("english")),
            ("Arabic", model_stats.get("arabic")),
        ):
            if stats is None:
                continue
            for field, scores in stats["per_field"].items():
                lines.append(
                    f"| {scope} | {field} | {fmt(scores['precision'])} "
                    f"| {fmt(scores['recall'])} | {fmt(scores['f1'])} | {scores['n']} |"
                )
    return "\n".join(lines)


def save_markdown_report(summary: Dict[str, dict], out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(render_markdown_report(summary), encoding="utf-8")
