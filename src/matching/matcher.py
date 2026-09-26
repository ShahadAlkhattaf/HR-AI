"""Interface for future matching implementations using an LLM client."""

from abc import ABC, abstractmethod

from ..llm.base import LLMClient
from .schema import MatchRequest


class JobMatcher(ABC):
    def __init__(self, client: LLMClient):
        self.client = client

    @abstractmethod
    def match(self, request: MatchRequest) -> object:
        """Match a CandidateProfile with a job description."""
