"""Minimal provider boundary for the single-call baseline."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelGatewayError(RuntimeError):
    """Raised when the configured model provider cannot return a response."""


@dataclass(frozen=True)
class ModelCompletion:
    """Raw provider output and auditable, non-secret invocation metadata."""

    raw_response: str
    provider: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None


class ModelGateway(Protocol):
    """The baseline may make exactly one call through this boundary."""

    def complete_json(self, *, system_prompt: str, user_prompt: str, schema: dict) -> ModelCompletion: ...


class OpenAIChatCompletionsGateway:
    """OpenAI-compatible structured-output gateway implemented without an SDK dependency."""

    def __init__(self, *, api_key: str, model: str, timeout_seconds: float = 60.0) -> None:
        if not api_key:
            raise ValueError("OpenAI API key must not be empty")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def complete_json(self, *, system_prompt: str, user_prompt: str, schema: dict) -> ModelCompletion:
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "baseline_action_response",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        request = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise ModelGatewayError(f"provider returned HTTP {error.code}: {detail}") from error
        except (URLError, TimeoutError) as error:
            raise ModelGatewayError(f"provider request failed: {error}") from error
        except json.JSONDecodeError as error:
            raise ModelGatewayError("provider returned invalid JSON") from error

        try:
            content = body["choices"][0]["message"]["content"]
            usage = body.get("usage") or {}
        except (IndexError, KeyError, TypeError) as error:
            raise ModelGatewayError("provider response did not contain one assistant message") from error
        if not isinstance(content, str):
            raise ModelGatewayError("provider response content was not text")

        return ModelCompletion(
            raw_response=content,
            provider="openai",
            model=str(body.get("model") or self._model),
            prompt_tokens=_as_optional_int(usage.get("prompt_tokens")),
            completion_tokens=_as_optional_int(usage.get("completion_tokens")),
        )


def _as_optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None
