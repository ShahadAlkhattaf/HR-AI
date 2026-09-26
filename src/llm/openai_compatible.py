"""OpenAI-compatible transport for the separately served model."""

from __future__ import annotations

import os
import time

from openai import APIConnectionError, OpenAI

from .base import LLMClient


class OpenAICompatibleClient(LLMClient):
    def __init__(self, model_id: str, base_url: str, api_key: str | None = None):
        self.model_id = model_id
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY", "not-needed")

    def _request(self, prompt: str, max_tokens: int) -> str:
        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model_id,
            max_tokens=max_tokens,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    def complete(self, prompt: str, max_tokens: int) -> str:
        for attempt in range(2):
            try:
                return self._request(prompt, max_tokens)
            except APIConnectionError:
                if attempt == 1:
                    raise
                time.sleep(0.25)
        raise AssertionError("unreachable")

