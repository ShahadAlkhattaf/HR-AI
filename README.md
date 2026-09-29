# HR AI — Bilingual Resume Parsing & Model Benchmarking

HR AI is a bilingual resume parsing and structured information extraction system developed as part of the SDA AI Data Center Bootcamp Capstone.

The project processes English and Arabic resumes, extracts candidate information into a structured JSON profile, benchmarks multiple language models against ground-truth data, and supports deployment through an OpenAI-compatible model serving endpoint.

## Overview

The system provides:

- PDF and DOCX resume parsing
- English and Arabic language support
- OCR fallback for scanned documents
- LLM-based structured candidate extraction
- JSON schema validation
- Model benchmarking and evaluation
- Per-field Precision, Recall, and F1 metrics
- Separate English and Arabic evaluation results
- Latency and token-usage measurements
- FastAPI backend
- React/Vite frontend
- OpenAI-compatible model serving integration
- Docker and Kubernetes-ready backend deployment

## Architecture

```text
User
  |
  v
React / Vite UI
  |
  v
FastAPI Backend
  |
  +--> Resume Parsing
  |      |- PDF / DOCX extraction
  |      |- OCR fallback
  |      `- Language detection
  |
  +--> Structured Extraction
  |      `- Prompt + CandidateProfile validation
  |
  v
OpenAI-Compatible Model Endpoint
  |
  v
vLLM / Qwen
```

The frontend and backend are independent. The evaluation pipeline can run without the frontend.

## Project Structure

```text
.
├── src/
│   ├── api/              # FastAPI application
│   ├── evaluation/       # Metrics, evaluator, and reports
│   ├── extraction/       # LLM extraction and CandidateProfile schema
│   ├── llm/              # Model client and serving configuration
│   ├── matching/         # Evaluation/scoring utilities
│   ├── parsing/          # PDF, DOCX, OCR, and parsing pipeline
│   └── utils/            # Language and text utilities
│
├── scripts/
│   ├── run_evaluation.py
│   ├── run_pipeline.py
│   ├── inspect_extractions.py
│   └── seed_sample_data.py
│
├── tests/                # Automated tests
├── ui/                   # React/Vite frontend
├── docker/               # Backend Docker configuration
├── configs/              # Project configuration
├── data/                 # Local evaluation data (not committed)
├── reports/              # Generated evaluation reports (not committed)
├── .env.example
└── requirements.txt
```

## Candidate Profile

The extraction pipeline converts a resume into structured fields including:

- Full name
- Email
- Phone
- Location
- Professional summary
- Skills
- Education
- Work experience
- Certifications
- Projects
- Languages
- Years of experience
- GitHub, LinkedIn, and portfolio links

Example:

```json
{
  "full_name": "Candidate Name",
  "email": "candidate@example.com",
  "skills": [
    "Python",
    "Docker",
    "Kubernetes"
  ],
  "education": [],
  "work_experience": [],
  "certificates": [],
  "projects": [],
  "languages": [
    {
      "language": "Arabic",
      "proficiency": "Native"
    }
  ]
}
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd beamdata-hr-ai-baseline
```

### 2. Create a Python environment

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

## Run the Backend

From the project root:

```bash
uvicorn src.api.main:app --reload --port 8000
```

Health check:

```text
GET /health
```

Available models:

```text
GET /v1/models
```

Resume parsing:

```text
POST /v1/resumes/parse
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Run the Frontend

```bash
cd ui
npm install
npm run dev
```

The development UI is normally available at:

```text
http://localhost:5173
```

Set the API endpoint in the UI to the running FastAPI backend, for example:

```text
http://127.0.0.1:8000
```

## Evaluation

The evaluation pipeline is independent of the frontend.

Evaluation data is kept locally under `data/` and is intentionally excluded from Git because resumes may contain personally identifiable information.

Run the benchmark with:

```bash
python scripts/run_evaluation.py
```

Language-specific evaluation is also supported:

```bash
python scripts/run_evaluation.py --language en
python scripts/run_evaluation.py --language ar
```

Generated reports are written under:

```text
reports/
```

The evaluation compares extracted CandidateProfile fields against ground-truth profiles and reports:

- JSON validity
- Precision
- Recall
- F1
- Per-field F1
- English F1
- Arabic F1
- Average latency
- Prompt tokens
- Completion tokens
- Total tokens

## Model Benchmark

The evaluation dataset contained:

- **44 resumes total**
- **36 English resumes**
- **8 Arabic resumes**

Three Qwen models were evaluated using the same extraction pipeline and ground-truth dataset.

| Model | JSON Validity | Precision | Recall | F1 | Avg Latency |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B-Instruct-AWQ | 40.9% | 0.6670 | 0.6125 | 0.6250 | 10.66 s |
| Qwen2.5-3B-Instruct | 72.7% | 0.7002 | 0.6890 | 0.6887 | 24.80 s |
| Qwen2.5-7B-Instruct | 100% | 0.7566 | 0.7440 | 0.7465 | 47.44 s |

### Language Results

| Model | English F1 | Arabic F1 |
|---|---:|---:|
| Qwen2.5-1.5B-Instruct-AWQ | 0.6860 | 0.5031 |
| Qwen2.5-3B-Instruct | 0.7195 | 0.5550 |
| Qwen2.5-7B-Instruct | 0.7832 | 0.5811 |

### Structured Output Reliability

Valid structured outputs:

```text
Qwen2.5-1.5B-Instruct-AWQ   18 / 44
Qwen2.5-3B-Instruct         32 / 44
Qwen2.5-7B-Instruct         44 / 44
```

Based on extraction quality and structured-output reliability, **Qwen2.5-7B-Instruct was selected for the final serving configuration**, with higher latency accepted as a trade-off for improved extraction performance.

## Testing

Run the automated tests with:

```bash
pytest
```

The test suite covers areas including:

- Parsing and normalization
- CandidateProfile validation
- Date normalization
- Evaluation metrics and reporting
- Model connection/fallback behavior
- Failed-evaluation retry behavior

## Docker

The backend can be built from the provided Docker configuration.

```bash
docker build -f docker/Dockerfile -t hr-ai-api .
```

Run it with the required environment configuration:

```bash
docker run --env-file .env -p 8000:8000 hr-ai-api
```

Evaluation datasets, reports, local environment files, frontend dependencies, and generated outputs are excluded from the production Docker context.

The current backend image does not build or serve the React frontend.

## Deployment Architecture

The intended production architecture keeps the application and inference layers separated:

```text
Browser
   |
   v
Frontend
   |
   v
HR AI FastAPI
   |
   v
Internal Model Service
   |
   v
vLLM + Qwen2.5-7B-Instruct
```

In Kubernetes, the API can communicate with the model server through its internal service address rather than exposing the inference endpoint directly to the browser.

## Privacy

Candidate resumes may contain personally identifiable information (PII).

Resume data is processed only as needed for parsing, skill extraction, and candidate analysis. Local resume datasets, generated candidate profiles, environment files, and evaluation outputs are excluded from version control.

## Notes

- The frontend never receives the model API credential.
- Model credentials are loaded by the backend from environment variables.
- Evaluation data and generated reports are not included in the repository.
- The frontend is not required to run model evaluation.
