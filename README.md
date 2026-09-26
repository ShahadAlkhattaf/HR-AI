# Beamdata HR AI — Bilingual Resume Parsing & Multi-Model Evaluation Baseline

Team 4 (HR AI) capstone baseline. Implements the pipeline required by the project spec, in priority order:

1. Parsing pipeline (bilingual EN/AR, modular, model-independent)
2. English + Arabic support
3. Evaluation dataset structure
4. Multiple-model evaluation via a common interface
5. Extensible quality/infrastructure metrics
6. Model-selection-ready report output
7. Thin FastAPI baseline around the pipeline

Docker, model serving, and deployment are the next stage.

## Architecture

```text
Resume (PDF/DOCX upload or file path)
  ↓
File Parser          (src/parsing/file_parser.py)
  │                   PDF: PyMuPDF / DOCX: python-docx
  ↓
OCR fallback         (src/parsing/ocr.py)
  │                   Tesseract, lang="ara+eng"
  ↓
Clean / normalize    (src/utils/language.py)
  │                   language detection, Arabic normalization, text cleaning
  ↓
[ Model A | Model B | Model C ]   (src/extraction/* + src/llm/*)
  │                                common ResumeExtractionModel interface
  ↓
Structured CandidateProfile JSON  (src/extraction/schema.py)
  ↓
Evaluation vs ground truth         (src/evaluation/*)
  ↓
FastAPI baseline                   (src/api/main.py)
                                      thin HTTP wrapper for local testing
                                      and future HR-app integration
```

### Why it is split this way

`src/parsing` does not depend on a specific model implementation, and the model layer operates on cleaned resume text rather than handling files directly.

The evaluator (`src/evaluation/evaluator.py`) and API layer (`src/api/main.py`) wire the stages together.

Existing registered models can therefore be selected through `configs/models.yaml` without changing the parsing or evaluation pipeline. Shared served-model clients are configured in `src/llm/registry.py`; extraction models are registered in `src/extraction/extractor.py`.

## Candidate Schema

`src/extraction/schema.py::CandidateProfile` approximates the target HR AI application's demo sections until the real API contract is available.

### Profile

- `full_name`
- `email`
- `phone`
- `location`
- `summary`
- `github`
- `linkedin`
- `portfolio`

### Skills

- `skills` — single flat list of strings

### Certificates

`certificates[]`

- `name`
- `issuer`
- `issue_date`
- `expiry_date`

### Projects

`projects[]`

- `name`
- `link`
- `description`

### Education

`education[]`

- `degree`
- `institution`
- `start_year`
- `end_year`
- `gpa`

### Experience

`work_experience[]`

- `company`
- `role`
- `start_date`
- `end_date`
- `description`

### Additional fields

- `languages[]`
- `years_of_experience`
- `detected_source_language`

Missing optional fields do not cause validation failure. Scalar fields default to `null` where appropriate and collections default to `[]`.

The current field names approximate the HR AI demo only. Once the real application API contract is provided, the API layer/schema mapping can be adapted without redesigning the parsing or model-serving pipeline.

## Supported Formats & Languages

### File formats

- PDF
- DOCX

### Languages

- English
- Arabic
- Mixed English/Arabic

OCR fallback uses Tesseract with `ara+eng` when native extraction produces insufficient text, such as scanned PDF pages.

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt --break-system-packages
```

Or use a Python virtual environment.

OCR fallback also requires system packages:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-ara poppler-utils
```

## Model Configuration

The `mock` model requires no API key and is intended only for smoke testing.

Real candidate models can be configured through environment variables.

Example:

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_COMPATIBLE_API_KEY=...

export QWEN_72B_BASE_URL=http://localhost:8000/v1
export QWEN_7B_BASE_URL=http://localhost:8001/v1

export DEFAULT_MODEL_KEY=mock
```

Model IDs and serving URLs can also be overridden through their corresponding environment variables defined in `src/llm/registry.py`.

Do not commit API keys or other secrets to the repository.

## Quickstart

### 1. Create bilingual smoke-test data

```bash
python scripts/seed_sample_data.py
```

This creates separate English and Arabic sample resumes with language-matched ground truth.

### 2. Test the parsing pipeline

English:

```bash
python scripts/run_pipeline.py data/resumes/english/sample_en_001.docx
```

Arabic:

```bash
python scripts/run_pipeline.py data/resumes/arabic/sample_ar_001.docx
```

This tests parsing independently from model inference.

### 3. Run the evaluation loop with the mock model

Create a temporary mock-only configuration:

```bash
python -c "
import yaml
yaml.safe_dump(
    {
        'models': ['mock'],
        'data_dir': 'data',
        'report_out_json': 'reports/eval_report.json',
        'report_out_md': 'reports/eval_report.md'
    },
    open('configs/mock_only.yaml', 'w')
)
"
```

Run:

```bash
python scripts/run_evaluation.py --config configs/mock_only.yaml
```

The mock model validates the end-to-end software path but does **not** measure real extraction quality.

### 4. Start the FastAPI baseline

```bash
uvicorn src.api.main:app --reload
```

The API will be available locally at:

```text
http://127.0.0.1:8000
```

## Adding Real Evaluation Data

Evaluation data follows this structure:

```text
data/
├── resumes/
│   ├── english/
│   └── arabic/
├── jobs/
└── ground_truth/
    └── <resume_id>.json
```

Each resume must have its own human-reviewed ground-truth JSON.

For example:

```text
sample_en_001.docx
        ↓
sample_en_001.json
```

The expected JSON follows the `CandidateProfile` schema.

Each ground-truth file must represent the information contained in that specific resume and preserve the appropriate source language.

Ground truth is used **only for evaluation** and is never provided to the model during inference.

The synthetic samples generated by `scripts/seed_sample_data.py` are smoke-test data, not the final benchmarking dataset.

## Adding a Candidate Model

All candidate models implement the same interface:

```text
ResumeExtractionModel
        ↓
_call(prompt)
        ↓
raw model response
        ↓
CandidateProfile
```

To add a new model:

1. Add a shared client under `src/llm/` if a new transport is needed.
2. Implement the extraction task under `src/extraction/` using `ResumeExtractionModel`.
3. Register the shared client in `src/llm/registry.py` and the extraction model in `src/extraction/extractor.py`.
4. Add its key to `configs/models.yaml`.

OpenAI-compatible candidates can reuse `OpenAICompatibleClient` with `OpenAICompatibleModel`, allowing models served through systems such as vLLM to be changed mainly through configuration rather than new integration code. Future job matching accepts a `CandidateProfile` and job description through `src/matching/`; its prompt and deterministic scoring are separate from extraction.

## Evaluation Metrics

Currently implemented in `src/evaluation/metrics.py`:

- Field-level precision / recall / F1 using normalized exact matching
- Skills evaluated as order-independent sets
- Structured collections evaluated using a representative key:
  - Education → `institution`
  - Work experience → `company`
  - Certificates → `name`
  - Projects → `name`
  - Languages → `language`
- JSON structural validity
- Overall F1 per resume
- Aggregated model results
- English vs. Arabic result splits
- Per-call latency captured in `ExtractionResult`

The current evaluator is a **baseline scorer**. Structured fields are not yet scored across every sub-field, and aliases or semantic equivalents are not treated as matches.

For example, the current exact matcher may treat:

```text
AWS != Amazon Web Services
```

as different values.

Evaluation metrics should therefore be refined before reporting final model extraction accuracy.

### Infrastructure metrics planned for deployed models

Once real models are running, benchmarking can be extended with:

- p50 / p95 latency
- throughput
- GPU / VRAM requirements
- token usage
- inference cost
- deployment/resource requirements

These measurements should come from actual model-serving runs rather than fabricated or estimated benchmark results.

## API

The FastAPI layer wraps the existing parsing and model-extraction pipeline for local testing and future HR application integration.

The current API is a **baseline contract**, not necessarily the final HR AI application API contract.

### `GET /health`

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### `GET /v1/models`

```bash
curl http://127.0.0.1:8000/v1/models
```

Returns configured model keys without exposing credentials.

### `POST /v1/resumes/parse`

Accepts a PDF or DOCX resume as `multipart/form-data`.

Example:

```bash
curl -F "file=@data/resumes/english/sample_en_001.docx" \
  "http://127.0.0.1:8000/v1/resumes/parse?model=mock"
```

Processing flow:

```text
Uploaded Resume
      ↓
File Parser
      ↓
OCR fallback if required
      ↓
Cleaned Resume Text
      ↓
Selected ResumeExtractionModel
      ↓
CandidateProfile
      ↓
JSON Response
```

The response contains the selected model, parsing metadata, and structured candidate profile.

Unsupported file formats return an HTTP 400 response. Temporary uploaded files are cleaned up after processing.

## What's Intentionally Not Implemented Yet

The current repository focuses on the resume extraction and evaluation baseline.

Not yet implemented:

- Docker / Docker Compose
- vLLM model serving
- GPU configuration
- Kubernetes / Helm / HPA
- Beamdata AI Hub deployment
- Frontend/UI
- Database
- Job-to-candidate matching
- Skill-gap analysis
- Learning recommendations
- RAG integration, unless relevant to the final use-case scope
- Final HR AI application API integration

## Next Deployment Stage

The next stage is to move from the validated baseline into real model serving and benchmarking:

1. Containerize the FastAPI resume-processing service.
2. Serve the first open-weight candidate through an OpenAI-compatible endpoint such as vLLM.
3. Run real resume extraction through the same API/pipeline.
4. Evaluate multiple candidate models using the same human-reviewed dataset.
5. Compare extraction quality, JSON validity, English/Arabic performance, latency, throughput, resource requirements, and cost.
6. Select the model based on the evaluation results and deployment constraints.
7. Deploy the selected setup to Beamdata AI Hub.
8. Re-run the evaluation against the deployed endpoint to verify deployment performance.

The HR AI application can then consume the serving API. If its final request/response contract differs from this baseline, adapt the API mapping without changing the underlying parsing, evaluation, or model-serving architecture.

## Tests

Run:

```bash
python -m pytest tests/ -v
```

Current tests cover:

- English language detection
- Arabic language detection
- Mixed-language detection
- Arabic normalization
- Text cleaning
- CandidateProfile validation/defaults
- Basic evaluation metric behavior

The current test suite is primarily for baseline validation. Real PDF, scanned/OCR resumes, real model endpoints, and the final evaluation dataset should be added to the test/benchmark process as they become available.
