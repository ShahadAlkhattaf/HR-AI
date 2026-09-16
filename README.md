# Beamdata HR AI — Bilingual Resume Parsing & Multi-Model Evaluation Baseline

Team 4 (HR AI) capstone baseline. Implements the pipeline required by the
project spec, in priority order:

1. Parsing pipeline (bilingual EN/AR, modular, model-independent)
2. English + Arabic support
3. Evaluation dataset structure
4. Multiple-model evaluation via a common interface
5. Extensible quality/infrastructure metrics
6. Model-selection-ready report output
7. **No UI** — intentionally out of scope until the above is solid

## Architecture

```
Resume
  ↓
File Parser        (src/parsing/file_parser.py)   PDF (PyMuPDF) / DOCX (python-docx)
  ↓
OCR fallback        (src/parsing/ocr.py)           Tesseract, lang="ara+eng"
  ↓
Clean/normalize      (src/utils/language.py)       detect language, normalize Arabic, clean text
  ↓
[ Model A | Model B | Model C ]   (src/models/*)   common ResumeExtractionModel interface
  ↓
Structured Candidate JSON          (src/models/schema.py)
  ↓
Evaluation vs ground truth          (src/evaluation/*)
```

**Why it's split this way:** `src/parsing` never imports anything from
`src/models`, and `src/models` never imports anything from `src/parsing`.
The evaluator (`src/evaluation/evaluator.py`) is the only place that wires
them together. That's what makes "swap Model A for Model B" a one-line
change in `configs/models.yaml`, and what lets parser/OCR improvements ship
without retesting every model.

## Setup

```bash
pip install -r requirements.txt --break-system-packages   # or use a venv

# OCR fallback requires system packages (Arabic + English Tesseract, poppler for PDF rendering):
sudo apt-get install -y tesseract-ocr tesseract-ocr-ara poppler-utils
```

Set API keys as needed:
```bash
export ANTHROPIC_API_KEY=...          # for the claude-sonnet model
export OPENAI_COMPATIBLE_API_KEY=...  # for vLLM/TGI/HF/AI-Hub endpoints, if they require one
```

## Quickstart (zero cost, no API keys needed)

```bash
# 1. Seed a tiny bilingual sample resume + ground truth so you can see the
#    full pipeline run before adding real data.
python scripts/seed_sample_data.py

# 2. Inspect what the parser extracts for one file (debug parsing/OCR in isolation).
python scripts/run_pipeline.py data/resumes/arabic/sample_ar_001.docx

# 3. Run the full evaluation loop with the free mock model to sanity-check
#    the model interface -> evaluator -> report chain end to end.
python -c "
import yaml
yaml.safe_dump({'models': ['mock'], 'data_dir': 'data',
                 'report_out_json': 'reports/eval_report.json',
                 'report_out_md': 'reports/eval_report.md'},
                open('configs/mock_only.yaml', 'w'))
"
python scripts/run_evaluation.py --config configs/mock_only.yaml
```

Once you have real candidate models available (an Anthropic key, and/or a
vLLM endpoint serving an open-weight model), edit `configs/models.yaml` to
list them and run:

```bash
python scripts/run_evaluation.py
```

## Adding real data (requirement #4)

```text
data/
├── resumes/
│   ├── english/       # real English resumes (PDF/DOCX)
│   └── arabic/        # real Arabic resumes (PDF/DOCX)
├── jobs/               # job descriptions (used later for job-matching, out of scope for baseline)
└── ground_truth/
    └── <resume_id>.json   # human-reviewed expected CandidateProfile, one per resume
```

`<resume_id>` must match the resume's filename stem
(`sample_en_001.docx` → `sample_en_001.json`). See
`scripts/seed_sample_data.py` for the exact ground-truth JSON shape
(mirrors `src/models/schema.py::CandidateProfile`).

**No benchmark numbers are fabricated anywhere in this codebase** —
`avg_f1`, `json_validity_rate`, and latency in the report are always
computed from an actual run. If you see zeros (like in the mock-model
Quickstart above), that's because the mock model intentionally returns
empty fields — it's there to test plumbing, not to report real quality.

## Adding a new candidate model (requirement #3, #6)

1. Subclass `ResumeExtractionModel` in a new file under `src/models/`
   (see `src/models/claude_model.py` or `openai_compatible_model.py` as
   templates) and implement only `_call(self, prompt: str) -> str`.
2. Register it in `src/models/registry.py`.
3. Add its key to `configs/models.yaml`.

No changes to the parsing pipeline or evaluator are ever required.

## Evaluation metrics (requirement #5)

Currently implemented (`src/evaluation/metrics.py`):
- Field-level precision / recall / F1 (scalar fields, list-of-string
  fields like skills, and list-of-object fields like education/work
  history/certifications/languages)
- JSON structural validity rate
- Overall F1 per resume, aggregated per model, and split English vs. Arabic

Designed to be extended with (not yet implemented — plug in once models are
actually deployed for benchmarking):
- End-to-end latency (already captured per-call in `ExtractionResult.latency_seconds`,
  just needs aggregation into p50/p95)
- GPU/VRAM requirements, throughput, cost — add a small `InfraProfile`
  dataclass alongside `ResumeEvalResult` and populate it from your serving
  stack's metrics (vLLM exposes these via its own metrics endpoint)

## What's intentionally NOT here yet

- Any frontend/UI (per requirement #7 — stretch goal only, after everything above works)
- Job-to-candidate matching / skill-gap analysis (mentioned in the use-case
  brief as later scope; `data/jobs/` is scaffolded for this)
- RAG knowledge base (Deliverable 5 in the program-wide plan)
- Containerization / AI Hub deployment scripts (Deliverable 4 — do this
  once a model is actually selected from real evaluation results)

## Tests

```bash
python -m pytest tests/ -v
```

Covers language detection, Arabic normalization, text cleaning, and the
metrics scoring functions. Add resume fixtures + expand
`tests/test_pipeline.py` as real sample resumes are added.
