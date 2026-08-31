from __future__ import annotations

import json
from pathlib import Path

from climate_cascade.baseline import gateway as gateway_module
from climate_cascade.baseline.gateway import ModelCompletion, OpenAIChatCompletionsGateway
from climate_cascade.baseline.runner import BaselineFailureCode, BaselineRunStatus, run_baseline
from climate_cascade.domain import load_frozen_case

CASE_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "cases" / "nepal-emsr927-v1"
)


class StaticGateway:
    def __init__(self, response: dict | str) -> None:
        self.response = response
        self.call_count = 0
        self.system_prompt = ""
        self.user_prompt = ""
        self.schema: dict = {}

    def complete_json(self, *, system_prompt: str, user_prompt: str, schema: dict) -> ModelCompletion:
        self.call_count += 1
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.schema = schema
        return ModelCompletion(
            raw_response=self.response if isinstance(self.response, str) else json.dumps(self.response),
            provider="test-provider",
            model="test-model",
            prompt_tokens=123,
            completion_tokens=45,
        )


def valid_response(*, title: str = "Request human review of Timure access conditions.") -> dict:
    return {
        "schema_version": "1",
        "case_id": "nepal-emsr927-v1",
        "actions": [
            {
                "schema_version": "1",
                "action_id": "timure-access-review",
                "title": title,
                "location_ref": "aoi:timure",
                "owner_role": "incident_commander",
                "urgency": "immediate",
                "evidence_ids": ["cems-activation"],
                "status": "draft",
                "estimate": None,
            },
            {
                "schema_version": "1",
                "action_id": "bidur-impact-review",
                "title": "Review cited residential impact evidence around Bidur.",
                "location_ref": "aoi:bidur",
                "owner_role": "incident_commander",
                "urgency": "immediate",
                "evidence_ids": ["cems-activation"],
                "status": "draft",
                "estimate": None,
            },
        ],
        "limitations": [
            "Bharatpur remains a pending area with unknown impact coverage.",
            "The initiating mechanism remains preliminary and requires human review.",
        ],
    }


def test_baseline_makes_one_structured_call_and_preserves_the_exact_response() -> None:
    gateway = StaticGateway(valid_response())

    run = run_baseline(load_frozen_case(CASE_DIRECTORY), gateway)

    assert run.status is BaselineRunStatus.COMPLETED
    assert run.attempt_count == 1
    assert gateway.call_count == 1
    assert run.raw_response == json.dumps(valid_response())
    assert "no tools" not in gateway.system_prompt.lower()
    assert "Bharatpur" not in gateway.user_prompt
    assert "no browsing" in gateway.user_prompt.lower()
    assert gateway.schema["required"] == ["schema_version", "case_id", "actions", "limitations"]
    assert gateway.schema["$defs"]["ActionCandidate"]["required"] == [
        "schema_version",
        "action_id",
        "title",
        "location_ref",
        "owner_role",
        "urgency",
        "evidence_ids",
        "status",
        "estimate",
    ]
    assert '"default"' not in json.dumps(gateway.schema)
    assert run.response is not None
    assert run.response.actions[0].status.value == "draft"


def test_baseline_fails_closed_without_a_configured_gateway() -> None:
    run = run_baseline(load_frozen_case(CASE_DIRECTORY), None)

    assert run.status is BaselineRunStatus.FAILED
    assert run.attempt_count == 0
    assert run.failure_code is BaselineFailureCode.PROVIDER_NOT_CONFIGURED


def test_baseline_does_not_repair_invalid_model_json() -> None:
    gateway = StaticGateway("not-json")

    run = run_baseline(load_frozen_case(CASE_DIRECTORY), gateway)

    assert run.status is BaselineRunStatus.FAILED
    assert run.attempt_count == 1
    assert run.failure_code is BaselineFailureCode.MODEL_SCHEMA
    assert gateway.call_count == 1


def test_baseline_records_model_validation_errors_with_value_error_context() -> None:
    response = valid_response()
    response["actions"][1]["action_id"] = response["actions"][0]["action_id"]

    run = run_baseline(load_frozen_case(CASE_DIRECTORY), StaticGateway(response))

    assert run.status is BaselineRunStatus.FAILED
    assert run.failure_code is BaselineFailureCode.MODEL_SCHEMA
    assert "unique action_id" in (run.failure_detail or "")


def test_baseline_rejects_unknown_evidence_references_after_one_call() -> None:
    response = valid_response()
    response["actions"][0]["evidence_ids"] = ["invented-source"]
    gateway = StaticGateway(response)

    run = run_baseline(load_frozen_case(CASE_DIRECTORY), gateway)

    assert run.status is BaselineRunStatus.FAILED
    assert run.failure_code is BaselineFailureCode.OUTPUT_POLICY
    assert "unknown evidence" in (run.failure_detail or "")
    assert gateway.call_count == 1


def test_openai_gateway_omits_unsupported_temperature_parameter(monkeypatch) -> None:
    captured: dict = {}

    class FakeHttpResponse:
        def __enter__(self) -> "FakeHttpResponse":
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "model": "gpt-5-mini",
                    "choices": [{"message": {"content": json.dumps(valid_response())}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20},
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout: float) -> FakeHttpResponse:
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeHttpResponse()

    monkeypatch.setattr(gateway_module, "urlopen", fake_urlopen)
    gateway = OpenAIChatCompletionsGateway(api_key="test-key", model="gpt-5-mini")

    completion = gateway.complete_json(
        system_prompt="system",
        user_prompt="user",
        schema={"type": "object", "additionalProperties": False, "properties": {}, "required": []},
    )

    assert captured["payload"]["model"] == "gpt-5-mini"
    assert "temperature" not in captured["payload"]
    assert completion.prompt_tokens == 10
    assert completion.completion_tokens == 20
