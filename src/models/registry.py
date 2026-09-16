"""
Model registry.

Central place that maps a short config key -> a ResumeExtractionModel
instance. This is what makes "replacing Model A with Model B" a one-line
change: the evaluator just iterates over `get_models(["model_a", "model_b"])`
and never imports a concrete model class itself.

Add a new candidate model by adding one entry here.
"""
from __future__ import annotations

from typing import Dict, List

from .base import ResumeExtractionModel
from .mock_model import MockModel
from .claude_model import ClaudeModel
from .openai_compatible_model import OpenAICompatibleModel


def _build_registry() -> Dict[str, ResumeExtractionModel]:
    return {
        # Always available, zero cost - used for pipeline smoke tests.
        "mock": MockModel(),

        # Reference commercial frontier baseline (Deliverable 3 comparator).
        "claude-sonnet": ClaudeModel(model_id="claude-sonnet-4-6"),

        # Example large open-weight candidate served via vLLM/TGI/HF endpoint.
        # Point base_url at your actual serving endpoint once deployed.
        "qwen-72b": OpenAICompatibleModel(
            model_id="Qwen/Qwen2.5-72B-Instruct",
            base_url="http://localhost:8000/v1",
            display_name="qwen2.5-72b-instruct",
        ),

        # Example small open-weight candidate (distillation-style comparison).
        "qwen-7b": OpenAICompatibleModel(
            model_id="Qwen/Qwen2.5-7B-Instruct",
            base_url="http://localhost:8001/v1",
            display_name="qwen2.5-7b-instruct",
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
