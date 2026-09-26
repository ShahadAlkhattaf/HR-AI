"""Shared served-model client configuration."""

from __future__ import annotations

import os

from .base import LLMClient
from .openai_compatible import OpenAICompatibleClient


MODEL_BASE_URL = os.environ.get("MODEL_BASE_URL", "http://localhost:8000/v1")
MODEL_ID = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-3B-Instruct")

_CLIENTS: dict[str, LLMClient] = {
    "served-model": OpenAICompatibleClient(model_id=MODEL_ID, base_url=MODEL_BASE_URL),
}


def get_client(key: str) -> LLMClient:
    if key not in _CLIENTS:
        raise KeyError(f"Unknown model key '{key}'. Available: {list(_CLIENTS.keys())}")
    return _CLIENTS[key]


def available_clients() -> list[str]:
    return list(_CLIENTS.keys())

