"""Tests for model transport, extraction fallbacks, and response diagnostics."""

import json
from types import SimpleNamespace

import httpx
from openai import APIConnectionError, APITimeoutError, BadRequestError

from src.extraction.extractor import OpenAICompatibleModel
from src.llm.base import LLMResponse
from src.llm.openai_compatible import OpenAICompatibleClient


def _model():
    client = OpenAICompatibleClient("test-model", "http://localhost:8000/v1", api_key="test-key")
    return OpenAICompatibleModel(client)


def _resume_part(prompt):
    return prompt.split("RESUME TEXT:\n---\n", 1)[1].rsplit("\n---\n\nJSON:", 1)[0]


def test_successful_request_keeps_existing_parameters(monkeypatch):
    calls = []

    def fake_client(**kwargs):
        assert kwargs == {
            "base_url": "http://localhost:8000/v1",
            "api_key": "test-key",
            "timeout": 120.0,
            "max_retries": 0,
        }

        def create(**params):
            calls.append(params)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"full_name":"Ada"}'))],
                usage=SimpleNamespace(prompt_tokens=12, completion_tokens=4, total_tokens=16),
            )

        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    monkeypatch.setattr("src.llm.openai_compatible.OpenAI", fake_client)
    result = _model().extract("Ada resume text")

    assert result.json_valid is True
    assert result.profile.full_name == "Ada"
    assert (result.prompt_tokens, result.completion_tokens, result.total_tokens) == (12, 4, 16)
    assert len(calls) == 1
    assert calls[0]["model"] == "test-model"
    assert calls[0]["max_tokens"] == 2000
    assert calls[0]["temperature"] == 0
    assert calls[0]["messages"][0]["content"].endswith("Ada resume text\n---\n\nJSON:")


def test_connection_error_retries_model_call(monkeypatch, caplog):
    model = _model()
    calls = []

    def request(prompt, max_tokens):
        calls.append(max_tokens)
        if len(calls) == 1:
            raise APIConnectionError(
                request=httpx.Request("POST", "http://localhost:8000/v1/chat/completions")
            ) from httpx.ConnectError("connection refused")
        return LLMResponse('{"skills":["Python"]}')

    monkeypatch.setattr(model.client, "_request", request)
    monkeypatch.setattr("src.llm.openai_compatible.time.sleep", lambda _: None)
    result = model.extract("Python")

    assert calls == [2000, 2000]
    assert result.json_valid is True
    assert result.profile.skills == ["Python"]
    assert [record.message for record in caplog.records] == [
        "Model connection attempt 1/2 failed: ConnectError: connection refused"
    ]


def test_timeout_error_uses_the_same_single_retry(monkeypatch):
    model = _model()
    calls = []

    def request(prompt, max_tokens):
        calls.append(max_tokens)
        if len(calls) == 1:
            raise APITimeoutError(request=httpx.Request("POST", "http://localhost:8000/v1/chat/completions"))
        return LLMResponse('{"full_name":"Ada"}')

    monkeypatch.setattr(model.client, "_request", request)
    monkeypatch.setattr("src.llm.openai_compatible.time.sleep", lambda _: None)
    result = model.extract("Ada resume text")

    assert calls == [2000, 2000]
    assert result.json_valid is True
    assert result.profile.full_name == "Ada"


def test_persistent_connection_error_remains_invalid(monkeypatch, caplog):
    model = _model()
    calls = []

    def request(prompt, max_tokens):
        calls.append(max_tokens)
        raise APIConnectionError(
            request=httpx.Request("POST", "http://localhost:8000/v1/chat/completions")
        ) from httpx.ConnectError("connection reset")

    monkeypatch.setattr(model.client, "_request", request)
    monkeypatch.setattr("src.llm.openai_compatible.time.sleep", lambda _: None)
    result = model.extract("resume text")

    assert calls == [2000, 2000]
    assert result.json_valid is False
    assert result.error == "model call failed: Connection error."
    assert [record.message for record in caplog.records] == [
        "Model connection attempt 1/2 failed: ConnectError: connection reset",
        "Model connection attempt 2/2 failed: ConnectError: connection reset",
    ]


def test_truncated_json_retries_with_more_output_tokens(monkeypatch):
    model = _model()
    calls = []

    def request(prompt, max_tokens):
        calls.append(max_tokens)
        return LLMResponse('{"full_name":' if max_tokens == 2000 else '{"full_name":"Ada"}')

    monkeypatch.setattr(model.client, "_request", request)
    result = model.extract("Ada resume text")

    assert calls == [2000, 4000]
    assert result.json_valid is True
    assert result.profile.full_name == "Ada"


def test_token_usage_includes_existing_json_fallback_calls(monkeypatch):
    model = _model()

    def request(prompt, max_tokens):
        if max_tokens == 2000:
            return LLMResponse('{"full_name":', 10, 5, 15)
        return LLMResponse('{"full_name":"Ada"}', 12, 7, 19)

    monkeypatch.setattr(model.client, "_request", request)
    result = model.extract("Ada resume text")

    assert result.json_valid is True
    assert (result.prompt_tokens, result.completion_tokens, result.total_tokens) == (22, 12, 34)


def test_context_error_splits_resume_and_merges_valid_profiles(monkeypatch):
    model = _model()
    resume = "Name: Ada\n\n" + "X" * 600 + "\n\nSkills: Python"
    parts = []

    def request(prompt, max_tokens):
        part = _resume_part(prompt)
        parts.append(part)
        if len(part) == len(resume):
            response = httpx.Response(
                400,
                request=httpx.Request("POST", "http://localhost:8000/v1/chat/completions"),
            )
            raise BadRequestError("maximum context length exceeded", response=response, body=None)
        return LLMResponse(json.dumps({"full_name": "Ada"} if "Name: Ada" in part else {"skills": ["Python"]}))

    monkeypatch.setattr(model.client, "_request", request)
    result = model.extract(resume)

    assert result.json_valid is True
    assert result.profile.full_name == "Ada"
    assert result.profile.skills == ["Python"]
    assert "Name: Ada" in parts[1]
    assert "Skills: Python" in parts[2]
    assert len(parts) == 3


def test_malformed_json_can_fall_back_to_chunks(monkeypatch):
    model = _model()
    resume = "Name: Ada\n\n" + "X" * 600 + "\n\nSkills: Python"
    calls = []

    def request(prompt, max_tokens):
        part = _resume_part(prompt)
        calls.append((len(part), max_tokens))
        if len(part) == len(resume):
            return LLMResponse('{"full_name":')
        return LLMResponse(json.dumps({"full_name": "Ada"} if "Name: Ada" in part else {"skills": ["Python"]}))

    monkeypatch.setattr(model.client, "_request", request)
    result = model.extract(resume)

    assert result.json_valid is True
    assert result.profile.full_name == "Ada"
    assert result.profile.skills == ["Python"]
    assert calls[:2] == [(len(resume), 2000), (len(resume), 4000)]
    assert len(calls) == 4


def test_unrecoverable_context_error_fails_without_dropping_text(monkeypatch):
    model = _model()
    calls = []

    def request(prompt, max_tokens):
        calls.append(_resume_part(prompt))
        raise RuntimeError("maximum context length exceeded")

    monkeypatch.setattr(model.client, "_request", request)
    result = model.extract("Short resume")

    assert calls == ["Short resume"]
    assert result.json_valid is False
    assert result.profile is None
    assert result.error.startswith("model call failed:")


def test_schema_validation_failure_is_not_retried(monkeypatch):
    model = _model()
    calls = []

    def request(prompt, max_tokens):
        calls.append(max_tokens)
        return LLMResponse('{"languages":["English"]}')

    monkeypatch.setattr(model.client, "_request", request)
    result = model.extract("English")

    assert calls == [2000]
    assert result.json_valid is False
    assert result.error.startswith("JSON parse/validation failed:")
    assert result.raw_response == '{"languages":["English"]}'
