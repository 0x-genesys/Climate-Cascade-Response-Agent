"""Bounded response-supervisor call over verified source evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable, Literal

from pydantic import Field, ValidationError

from climate_cascade.baseline import ModelGateway
from climate_cascade.baseline.gateway import ModelGatewayError
from climate_cascade.baseline.schema import response_supervisor_response_schema
from climate_cascade.domain import (
    FrozenCaseBundle,
    Identifier,
    NonEmptyText,
    ResponseSupervisorActionResponse,
    StrictModel,
    VerifiedEvidencePackage,
)


class ResponseSupervisorRunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class ResponseSupervisorFailureCode(StrEnum):
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"
    PROVIDER_ERROR = "provider_error"
    MODEL_SCHEMA = "model_schema"
    OUTPUT_POLICY = "output_policy"


class ResponseSupervisorConfig(StrictModel):
    schema_version: Literal["1"] = "1"
    agent_id: Identifier
    version: NonEmptyText
    max_actions: int = Field(ge=1, le=5)
    system_prompt: NonEmptyText


class ResponseSupervisorRunArtifact(StrictModel):
    """Replayable supervisor request, response, and failure boundary."""

    schema_version: Literal["1"] = "1"
    run_id: str = Field(pattern=r"^run-[a-f0-9-]{36}$")
    case_id: Identifier
    status: ResponseSupervisorRunStatus
    started_at: datetime
    completed_at: datetime
    attempt_count: int = Field(ge=0, le=1)
    agent_id: Identifier
    agent_version: NonEmptyText
    source_package_id: Identifier
    system_prompt: str
    user_prompt: str
    prompt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider: str | None = None
    model: str | None = None
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    raw_response: str | None = None
    response: ResponseSupervisorActionResponse | None = None
    failure_code: ResponseSupervisorFailureCode | None = None
    failure_detail: str | None = None


def load_response_supervisor_config(path: Path) -> ResponseSupervisorConfig:
    return ResponseSupervisorConfig.model_validate_json(path.read_text(encoding="utf-8"))


def run_response_supervisor(
    *,
    run_id: str,
    case_id: str,
    evidence: VerifiedEvidencePackage,
    config: ResponseSupervisorConfig,
    gateway: ModelGateway | None,
    case: FrozenCaseBundle | None,
    now: Callable[[], datetime] | None = None,
) -> ResponseSupervisorRunArtifact:
    """Make one structured draft-only recommendation call using verified facts."""

    clock = now or (lambda: datetime.now(UTC))
    started_at = clock()
    user_prompt = _render_user_prompt(case_id=case_id, evidence=evidence, case=case, max_actions=config.max_actions)
    prompt_sha256 = sha256(f"{config.system_prompt}\n{user_prompt}".encode("utf-8")).hexdigest()
    common = {
        "run_id": run_id,
        "case_id": case_id,
        "started_at": started_at,
        "agent_id": config.agent_id,
        "agent_version": config.version,
        "source_package_id": evidence.package_id,
        "system_prompt": config.system_prompt,
        "user_prompt": user_prompt,
        "prompt_sha256": prompt_sha256,
    }
    if gateway is None:
        return ResponseSupervisorRunArtifact(
            **common,
            status=ResponseSupervisorRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=0,
            failure_code=ResponseSupervisorFailureCode.PROVIDER_NOT_CONFIGURED,
            failure_detail="No model gateway was configured for the response supervisor. No model request was attempted.",
        )

    try:
        completion = gateway.complete_json(
            system_prompt=config.system_prompt,
            user_prompt=user_prompt,
            schema=response_supervisor_response_schema(),
            schema_name="response_supervisor_action_response",
        )
    except ModelGatewayError as error:
        return ResponseSupervisorRunArtifact(
            **common,
            status=ResponseSupervisorRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=1,
            failure_code=ResponseSupervisorFailureCode.PROVIDER_ERROR,
            failure_detail=str(error),
        )

    try:
        response = ResponseSupervisorActionResponse.model_validate_json(completion.raw_response)
    except ValidationError as error:
        return ResponseSupervisorRunArtifact(
            **common,
            status=ResponseSupervisorRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=1,
            provider=completion.provider,
            model=completion.model,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            raw_response=completion.raw_response,
            failure_code=ResponseSupervisorFailureCode.MODEL_SCHEMA,
            failure_detail=_compact_validation_error(error),
        )

    response = _canonicalize_evidence_references(response, evidence=evidence)
    policy_failure = _validate_response(response, case_id=case_id, evidence=evidence, max_actions=config.max_actions)
    if policy_failure is not None:
        return ResponseSupervisorRunArtifact(
            **common,
            status=ResponseSupervisorRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=1,
            provider=completion.provider,
            model=completion.model,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            raw_response=completion.raw_response,
            response=response,
            failure_code=ResponseSupervisorFailureCode.OUTPUT_POLICY,
            failure_detail=policy_failure,
        )

    return ResponseSupervisorRunArtifact(
        **common,
        status=ResponseSupervisorRunStatus.COMPLETED,
        completed_at=clock(),
        attempt_count=1,
        provider=completion.provider,
        model=completion.model,
        prompt_tokens=completion.prompt_tokens,
        completion_tokens=completion.completion_tokens,
        raw_response=completion.raw_response,
        response=response,
    )


def _render_user_prompt(
    *, case_id: str, evidence: VerifiedEvidencePackage, case: FrozenCaseBundle | None, max_actions: int
) -> str:
    source_view = evidence.model_dump(mode="json", exclude={"snapshots": {"__all__": {"raw_content"}}})
    scenario = None
    if case is not None:
        scenario = {
            "scenario_id": case.scenario.scenario_id,
            "constraints": [constraint.model_dump(mode="json") for constraint in case.scenario.constraints],
        }
    payload = {
        "task": "Draft a small, human-reviewable response queue from verified source evidence.",
        "case_id": case_id,
        "maximum_actions": max_actions,
        "allowed_action_evidence_ids": [snapshot.snapshot_id for snapshot in evidence.snapshots],
        "source_evidence": source_view,
        "operational_scenario": scenario,
        "response_rules": [
            "For every action.evidence_ids value, use an exact value from allowed_action_evidence_ids. Do not use source_id or claim_id values.",
            "Every action is a draft for a qualified human; do not issue an order, dispatch, or public warning.",
            "Keep open activations, pending products, and preliminary facts visible as uncertainty.",
            "When data are missing, request evidence or verification rather than infer no impact.",
            "Set estimate to null, or use only a not_estimable estimate with a concrete abstention reason; never provide numeric estimates.",
            "Do not claim lives saved, casualty counts, or deterministic impact analysis.",
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _canonicalize_evidence_references(
    response: ResponseSupervisorActionResponse, *, evidence: VerifiedEvidencePackage
) -> ResponseSupervisorActionResponse:
    """Persist citations against immutable snapshots, accepting a source ID model alias."""

    snapshot_id_by_source_id = {snapshot.source_id: snapshot.snapshot_id for snapshot in evidence.snapshots}
    return response.model_copy(
        update={
            "actions": [
                action.model_copy(
                    update={
                        "evidence_ids": [
                            snapshot_id_by_source_id.get(evidence_id, evidence_id) for evidence_id in action.evidence_ids
                        ]
                    }
                )
                for action in response.actions
            ]
        }
    )


def _validate_response(
    response: ResponseSupervisorActionResponse, *, case_id: str, evidence: VerifiedEvidencePackage, max_actions: int
) -> str | None:
    if response.case_id != case_id:
        return "response.case_id does not match the run case"
    if len(response.actions) > max_actions:
        return f"response contains more than configured maximum {max_actions} actions"
    known_evidence_ids = {snapshot.snapshot_id for snapshot in evidence.snapshots}
    unknown = sorted(
        {
            evidence_id
            for action in response.actions
            for evidence_id in action.evidence_ids
            if evidence_id not in known_evidence_ids
        }
    )
    if unknown:
        return f"response references unknown evidence IDs: {unknown}"
    return None


def _compact_validation_error(error: ValidationError) -> str:
    # Pydantic keeps model-validator exceptions in `ctx.error`; serialize them as text for a durable artifact.
    return json.dumps(error.errors(include_url=False), separators=(",", ":"), default=str)[:2000]
