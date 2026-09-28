"""OpenAI-compatible transport for the separately served model."""

from __future__ import annotations

import logging
import os
import time

from openai import APIConnectionError, OpenAI

from .base import LLMClient, LLMResponse


logger = logging.getLogger(__name__)


class OpenAICompatibleClient(LLMClient):
    def __init__(self, model_id: str, base_url: str, api_key: str | None = None):
        self.model_id = model_id
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY", "not-needed")

    def _request(self, prompt: str, max_tokens: int) -> LLMResponse:
        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=120.0,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=self.model_id,
            max_tokens=max_tokens,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=response.choices[0].message.content or "",
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )

    def complete(self, prompt: str, max_tokens: int) -> LLMResponse:
        for attempt in range(2):
            try:
                return self._request(prompt, max_tokens)
            except APIConnectionError as error:
                cause = error.__cause__
                logger.warning(
                    "Model connection attempt %d/2 failed: %s: %s",
                    attempt + 1,
                    type(cause).__name__,
                    str(cause),
                )
                if attempt == 1:
                    raise
                time.sleep(0.25)
        raise AssertionError("unreachable")

