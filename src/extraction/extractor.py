"""Resume extraction interface and registered extraction models."""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..llm.base import LLMResponse
from ..llm.openai_compatible import OpenAICompatibleClient
from ..llm.registry import available_clients, get_client
from .prompt import build_extraction_prompt
from .schema import CandidateProfile


@dataclass
class ExtractionResult:
    """Profile and response diagnostics from one extraction attempt."""

    model_name: str
    profile: Optional[CandidateProfile]
    raw_response: str
    latency_seconds: float
    json_valid: bool
    error: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ResumeExtractionModel(ABC):

    name: str = "unnamed-model"

    @abstractmethod
    def _call(self, prompt: str) -> str:
        """Return raw model text for the extraction prompt."""
        raise NotImplementedError

    def build_prompt(self, resume_text: str) -> str:
        return build_extraction_prompt(resume_text)

    def extract(self, resume_text: str) -> ExtractionResult:
        prompt = self.build_prompt(resume_text)

        start = time.perf_counter()
        try:
            raw = self._call(prompt)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ExtractionResult(
                model_name=self.name,
                profile=None,
                raw_response="",
                latency_seconds=elapsed,
                json_valid=False,
                error=f"model call failed: {e}",
            )
        elapsed = time.perf_counter() - start

        cleaned = _strip_code_fences(raw)
        try:
            data = json.loads(cleaned)
            profile = CandidateProfile.model_validate(data)
            return ExtractionResult(
                model_name=self.name,
                profile=profile,
                raw_response=raw,
                latency_seconds=elapsed,
                json_valid=True,
            )
        except Exception as e:
            return ExtractionResult(
                model_name=self.name,
                profile=None,
                raw_response=raw,
                latency_seconds=elapsed,
                json_valid=False,
                error=f"JSON parse/validation failed: {e}",
            )


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


_DEFAULT_MAX_TOKENS = 2000
_RETRY_MAX_TOKENS = 4000
_MAX_SPLIT_DEPTH = 4
_MIN_CHUNK_CHARS = 256


class _InvalidResponse(Exception):
    def __init__(self, raw: str, cause: Exception):
        self.raw = raw
        self.cause = cause
        super().__init__(str(cause))


class _InvalidJSON(_InvalidResponse):
    pass


class _InvalidProfile(_InvalidResponse):
    pass


def _is_context_length_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        phrase in message
        for phrase in (
            "maximum context",
            "context length",
            "context window",
            "max_model_len",
            "max model len",
            "prompt is too long",
            "input is too long",
            "too many tokens",
            "token limit",
            "request too large",
            "payload too large",
        )
    )


def _split_resume_text(text: str) -> tuple[str, str]:
    midpoint = len(text) // 2
    lower, upper = len(text) // 4, 3 * len(text) // 4
    for separator in ("\n\n", "\n", " "):
        before = text.rfind(separator, lower, midpoint)
        after = text.find(separator, midpoint, upper)
        choices = [position for position in (before, after) if position >= 0]
        if choices:
            split_at = min(choices, key=lambda position: abs(position - midpoint))
            return text[:split_at].strip(), text[split_at + len(separator):].strip()
    return text[:midpoint].strip(), text[midpoint:].strip()


def _merge_profiles(profiles: list[CandidateProfile]) -> CandidateProfile:
    data = {}
    list_fields = {"skills", "certificates", "projects", "education", "work_experience", "languages"}
    profile_data = [profile.model_dump() for profile in profiles]
    for field in CandidateProfile.model_fields:
        values = [profile[field] for profile in profile_data]
        if field in list_fields:
            seen = set()
            merged = []
            for value in values:
                for item in value:
                    key = (
                        json.dumps(item, ensure_ascii=False, sort_keys=True)
                        if isinstance(item, dict)
                        else item.casefold()
                    )
                    if key not in seen:
                        seen.add(key)
                        merged.append(item)
            data[field] = merged
        elif field == "detected_source_language":
            languages = set(values)
            data[field] = (
                "mixed"
                if "mixed" in languages or {"en", "ar"}.issubset(languages)
                else next((value for value in values if value), None)
            )
        else:
            data[field] = next((value for value in values if value is not None and value != ""), None)
    return CandidateProfile.model_validate(data)


def _usage_totals(responses: list[LLMResponse]) -> dict[str, int | None]:
    fields = ("prompt_tokens", "completion_tokens", "total_tokens")
    return {
        field: sum(getattr(response, field) for response in responses)
        if responses and all(getattr(response, field) is not None for response in responses)
        else None
        for field in fields
    }


class OpenAICompatibleModel(ResumeExtractionModel):
    """Extraction task using a shared OpenAI-compatible client."""

    def __init__(self, client: OpenAICompatibleClient, display_name: str | None = None):
        self.client = client
        self.name = display_name or client.model_id

    def _call(self, prompt: str) -> str:
        return self.client.complete(prompt, _DEFAULT_MAX_TOKENS).content

    def _extract_once(
        self, resume_text: str, max_tokens: int, usage: list[LLMResponse]
    ) -> tuple[CandidateProfile, str]:
        prompt = self.build_prompt(resume_text)
        response = self.client.complete(prompt, max_tokens)
        usage.append(response)
        raw = response.content
        try:
            data = json.loads(_strip_code_fences(raw))
        except json.JSONDecodeError as error:
            raise _InvalidJSON(raw, error) from error
        try:
            return CandidateProfile.model_validate(data), raw
        except Exception as error:
            raise _InvalidProfile(raw, error) from error

    def _extract_with_fallback(
        self, resume_text: str, usage: list[LLMResponse], depth: int = 0
    ) -> tuple[CandidateProfile, list[str]]:
        try:
            profile, raw = self._extract_once(resume_text, _DEFAULT_MAX_TOKENS, usage)
            return profile, [raw]
        except _InvalidJSON:
            try:
                profile, raw = self._extract_once(resume_text, _RETRY_MAX_TOKENS, usage)
                return profile, [raw]
            except _InvalidJSON as error:
                failure = error
            except Exception as error:
                if not _is_context_length_error(error):
                    raise
                failure = error
        except Exception as error:
            if not _is_context_length_error(error):
                raise
            failure = error

        if depth >= _MAX_SPLIT_DEPTH or len(resume_text) < _MIN_CHUNK_CHARS:
            raise failure
        left, right = _split_resume_text(resume_text)
        if not left or not right:
            raise failure
        left_profile, left_raw = self._extract_with_fallback(left, usage, depth + 1)
        right_profile, right_raw = self._extract_with_fallback(right, usage, depth + 1)
        return _merge_profiles([left_profile, right_profile]), left_raw + right_raw

    def extract(self, resume_text: str) -> ExtractionResult:
        """Retry transport failures and fall back on context-length or JSON syntax errors."""
        start = time.perf_counter()
        usage: list[LLMResponse] = []
        try:
            profile, responses = self._extract_with_fallback(resume_text, usage)
            return ExtractionResult(
                model_name=self.name,
                profile=profile,
                raw_response=responses[0] if len(responses) == 1 else json.dumps(responses, ensure_ascii=False),
                latency_seconds=time.perf_counter() - start,
                json_valid=True,
                **_usage_totals(usage),
            )
        except _InvalidResponse as error:
            return ExtractionResult(
                model_name=self.name,
                profile=None,
                raw_response=error.raw,
                latency_seconds=time.perf_counter() - start,
                json_valid=False,
                error=f"JSON parse/validation failed: {error.cause}",
                **_usage_totals(usage),
            )
        except Exception as error:
            return ExtractionResult(
                model_name=self.name,
                profile=None,
                raw_response="",
                latency_seconds=time.perf_counter() - start,
                json_valid=False,
                error=f"model call failed: {error}",
                **_usage_totals(usage),
            )


from .mock_model import MockModel  # noqa: E402

_REGISTRY: dict[str, ResumeExtractionModel] = {
    "mock": MockModel(),
    "served-model": OpenAICompatibleModel(get_client("served-model")),
}


def get_model(key: str) -> ResumeExtractionModel:
    if key not in _REGISTRY:
        raise KeyError(f"Unknown model key '{key}'. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[key]


def get_models(keys: list[str]) -> dict[str, ResumeExtractionModel]:
    return {key: get_model(key) for key in keys}


def available_models() -> list[str]:
    return ["mock", *available_clients()]
