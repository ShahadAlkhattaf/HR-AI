"""Transport interface shared by extraction and future matching tasks."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, max_tokens: int) -> LLMResponse:
        """Return text and any usage reported by the same model response."""

