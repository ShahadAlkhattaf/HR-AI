"""
Model A (reference commercial frontier candidate): Anthropic Claude.

Any other model - open-weight served via vLLM/TGI, a Hugging Face
serverless endpoint, an OpenAI-compatible endpoint, etc. - plugs in the
same way: subclass ResumeExtractionModel and implement `_call`.
"""
from __future__ import annotations

import os

from .base import ResumeExtractionModel


class ClaudeModel(ResumeExtractionModel):
    def __init__(self, model_id: str = "claude-sonnet-4-6", api_key: str | None = None):
        self.name = model_id
        self._model_id = model_id
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def _call(self, prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model=self._model_id,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )
