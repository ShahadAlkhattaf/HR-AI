"""
Model B / Model C (open-weight candidates): any OpenAI-compatible endpoint.

Covers vLLM, TGI, Hugging Face Inference Endpoints, and eventually Beamdata
AI Hub's own serving endpoint once the selected model is deployed there —
all of these commonly expose an OpenAI-compatible /chat/completions API.
Swapping between a large open-weight model (e.g. Qwen2.5-72B) and a small
one (e.g. Qwen2.5-7B) is just a different `base_url` / `model_id`, no code
changes required, which is the point of the common interface.
"""
from __future__ import annotations

import os

from .base import ResumeExtractionModel


class OpenAICompatibleModel(ResumeExtractionModel):
    def __init__(
        self,
        model_id: str,
        base_url: str,
        api_key: str | None = None,
        display_name: str | None = None,
    ):
        self.name = display_name or model_id
        self._model_id = model_id
        self._base_url = base_url
        self._api_key = api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY", "not-needed")

    def _call(self, prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model_id,
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
