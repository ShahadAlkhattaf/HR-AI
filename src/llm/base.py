"""Transport interface shared by extraction and future matching tasks."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, max_tokens: int) -> str:
        """Return the model's raw text response for a task-specific prompt."""

