"""
Thin FastAPI baseline around the existing parsing + model pipeline.

    upload (PDF/DOCX)
      -> existing parsing pipeline (src/parsing)
      -> selected ResumeExtractionModel (src/models/registry.py)
      -> CandidateProfile
      -> JSON response

This is a baseline contract for local testing and for wiring up the
eventual HR AI application, NOT the final agreed-upon API contract for
that application. Endpoint paths/shape are deliberately simple so they're
easy to adapt once the real contract is available.

Run locally:
    uvicorn src.api.main:app --reload
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..models.claude_model import ClaudeModel
from ..models.openai_compatible_model import OpenAICompatibleModel
from ..models.registry import available_models, get_model
from ..parsing.file_parser import UnsupportedFileTypeError
from ..parsing.pipeline import run_parsing_pipeline

# Model used when the caller doesn't specify one. Defaults to the free mock
# model so the API is usable out of the box without any API keys; override
# via env var once a real candidate model is configured/selected.
DEFAULT_MODEL_KEY = os.environ.get("DEFAULT_MODEL_KEY", "mock")

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

app = FastAPI(
    title="Beamdata HR AI — Resume Extraction API (baseline)",
    version="0.1.0",
    description=(
        "Baseline endpoints wrapping the bilingual resume parsing pipeline "
        "and the multi-model extraction layer. Intended for local testing "
        "and as a starting point for the real HR AI application contract."
    ),
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict:
    """Lists configured extraction model keys without exposing any secrets
    (API keys, base URLs with credentials, etc.).
    """
    models_info = []
    for key in available_models():
        try:
            model = get_model(key)
        except KeyError:
            continue
        if isinstance(model, ClaudeModel):
            model_type = "anthropic"
        elif isinstance(model, OpenAICompatibleModel):
            model_type = "openai-compatible"
        else:
            model_type = "mock"
        models_info.append(
            {
                "key": key,
                "name": model.name,
                "type": model_type,
            }
        )
    return {"models": models_info, "default": DEFAULT_MODEL_KEY}


@app.post("/v1/resumes/parse")
async def parse_resume(file: UploadFile = File(...), model: str | None = None) -> JSONResponse:
    """Parses an uploaded PDF/DOCX resume and returns a CandidateProfile.

    `model` is an optional query parameter selecting a registered model key
    from /v1/models. It defaults to DEFAULT_MODEL_KEY.
    """
    model_key = model or DEFAULT_MODEL_KEY

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix or 'unknown'}'. "
                f"Only PDF and DOCX are supported."
            ),
        )

    try:
        extraction_model = get_model(model_key)
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{model_key}'. See GET /v1/models for available keys.",
        )

    tmp_path: str | None = None
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            parsed = run_parsing_pipeline(tmp_path)
        except UnsupportedFileTypeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse resume: {e}")

        extraction = extraction_model.extract(parsed.clean_text)
        if not extraction.json_valid or extraction.profile is None:
            raise HTTPException(
                status_code=502,
                detail=f"Model '{model_key}' did not return valid structured output: {extraction.error}",
            )

        return JSONResponse(
            content={
                "model": model_key,
                "detected_language": parsed.detected_language,
                "extraction_method": parsed.extraction_method,
                "profile": extraction.profile.model_dump(),
            }
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
