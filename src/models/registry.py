"""
Model registry.

The registry exposes a stable `served-model` key to the application and
evaluation pipeline. The actual model served behind that key is selected
through environment variables.

This allows candidate models to be changed without modifying application
code or rebuilding the application image.

Examples:
    Qwen/Qwen2.5-3B-Instruct
    Qwen/Qwen2.5-7B-Instruct
    google/gemma-2-2b-it
"""

from __future__ import annotations

import os
from typing import Dict, List

from .base import ResumeExtractionModel
from .mock_model import MockModel
from .openai_compatible_model import OpenAICompatibleModel


MODEL_BASE_URL = os.environ.get(
    "MODEL_BASE_URL",
    "http://localhost:8000/v1",
)

MODEL_ID = os.environ.get(
    "MODEL_ID",
    "Qwen/Qwen2.5-3B-Instruct",
)


def _build_registry() -> Dict[str, ResumeExtractionModel]:
    return {
        # Always available, used for pipeline smoke tests.
        "mock": MockModel(),

        # Real model served through an OpenAI-compatible endpoint.
        "served-model": OpenAICompatibleModel(
            name=MODEL_ID,
            model_id=MODEL_ID,
            base_url=MODEL_BASE_URL,
        ),
    }


_REGISTRY = _build_registry()


def get_model(key: str) -> ResumeExtractionModel:
    if key not in _REGISTRY:
        raise KeyError(
            f"Unknown model key '{key}'. Available: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[key]


def get_models(keys: List[str]) -> Dict[str, ResumeExtractionModel]:
    return {k: get_model(k) for k in keys}


def available_models() -> List[str]:
    return list(_REGISTRY.keys())