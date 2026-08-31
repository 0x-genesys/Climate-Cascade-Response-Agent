"""Execute and preserve one direct-prompt baseline attempt."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
from typing import Callable, Literal
from uuid import uuid4

from pydantic import Field, ValidationError

from climate_cascade.domain import BaselineActionResponse, FrozenCaseBundle, Identifier, StrictModel, VerifiedEvidencePackage

from .gateway import ModelGateway, ModelGatewayError
from .prompting import SYSTEM_PROMPT, render_live_user_prompt, render_user_prompt
from .schema import baseline_response_schema


class BaselineRunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class BaselineFailureCode(StrEnum):
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"
    PROVIDER_ERROR = "provider_error"
    MODEL_SCHEMA = "model_schema"
    OUTPUT_POLICY = "output_policy"


class BaselineRunArtifact(StrictModel):
    """Self-contained run artifact for reproducible baseline evaluation."""

    schema_version: Literal["1"] = "1"
    run_id: str = Field(pattern=r"^baseline-[a-f0-9-]{36}$")
    case_id: Identifier
    status: BaselineRunStatus
    started_at: datetime
    completed_at: datetime
    attempt_count: int = Field(ge=0, le=1)
    system_prompt: str
    user_prompt: str
    prompt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider: str | None = None
    model: str | None = None
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    raw_response: str | None = None
    response: BaselineActionResponse | None = None
    failure_code: BaselineFailureCode | None = None
    failure_detail: str | None = None


def run_baseline(
    case: FrozenCaseBundle,
    gateway: ModelGateway | None,
    *,
    now: Callable[[], datetime] | None = None,
) -> BaselineRunArtifact:
    """Run exactly one model request, never attempting schema repair or retries."""

    clock = now or (lambda: datetime.now(UTC))
    started_at = clock()
    user_prompt = render_user_prompt(case)
    prompt_sha256 = sha256(f"{SYSTEM_PROMPT}\n{user_prompt}".encode("utf-8")).hexdigest()
    common = {
        "run_id": f"baseline-{uuid4()}",
        "case_id": case.manifest.fixture_id,
        "started_at": started_at,
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": user_prompt,
        "prompt_sha256": prompt_sha256,
    }
    if gateway is None:
        return BaselineRunArtifact(
            **common,
            status=BaselineRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=0,
            failure_code=BaselineFailureCode.PROVIDER_NOT_CONFIGURED,
            failure_detail="No model gateway was configured. No model request was attempted.",
        )

    try:
        completion = gateway.complete_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=baseline_response_schema(),
        )
    except ModelGatewayError as error:
        return BaselineRunArtifact(
            **common,
            status=BaselineRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=1,
            failure_code=BaselineFailureCode.PROVIDER_ERROR,
            failure_detail=str(error),
        )

    try:
        response = BaselineActionResponse.model_validate_json(completion.raw_response)
    except ValidationError as error:
        return BaselineRunArtifact(
            **common,
            status=BaselineRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=1,
            provider=completion.provider,
            model=completion.model,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            raw_response=completion.raw_response,
            failure_code=BaselineFailureCode.MODEL_SCHEMA,
            failure_detail=_compact_validation_error(error),
        )

    policy_failure = _validate_response_against_case(response, case)
    if policy_failure:
        return BaselineRunArtifact(
            **common,
            status=BaselineRunStatus.FAILED,
            completed_at=clock(),
            attempt_count=1,
            provider=completion.provider,
            model=completion.model,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            raw_response=completion.raw_response,
            response=response,
            failure_code=BaselineFailureCode.OUTPUT_POLICY,
            failure_detail=policy_failure,
        )

    return BaselineRunArtifact(
        **common,
        status=BaselineRunStatus.COMPLETED,
        completed_at=clock(),
        attempt_count=1,
        provider=completion.provider,
        model=completion.model,
        prompt_tokens=completion.prompt_tokens,
        completion_tokens=completion.completion_tokens,
        raw_response=completion.raw_response,
        response=response,
    )


def run_live_baseline(
    *, case_id: str, evidence: VerifiedEvidencePackage, gateway: ModelGateway | None, now: Callable[[], datetime] | None = None
) -> BaselineRunArtifact:
    """Run the one-call baseline on an already-pinned live source snapshot."""

    clock = now or (lambda: datetime.now(UTC))
    started_at = clock()
    user_prompt = render_live_user_prompt(case_id=case_id, evidence=evidence)
    prompt_sha256 = sha256(f"{SYSTEM_PROMPT}\n{user_prompt}".encode("utf-8")).hexdigest()
    common = {
        "run_id": f"baseline-{uuid4()}", "case_id": case_id, "started_at": started_at,
        "system_prompt": SYSTEM_PROMPT, "user_prompt": user_prompt, "prompt_sha256": prompt_sha256,
    }
    if gateway is None:
        return BaselineRunArtifact(**common, status=BaselineRunStatus.FAILED, completed_at=clock(), attempt_count=0,
            failure_code=BaselineFailureCode.PROVIDER_NOT_CONFIGURED,
            failure_detail="No model gateway was configured. No model request was attempted.")
    try:
        completion = gateway.complete_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt, schema=baseline_response_schema())
    except ModelGatewayError as error:
        return BaselineRunArtifact(**common, status=BaselineRunStatus.FAILED, completed_at=clock(), attempt_count=1,
            failure_code=BaselineFailureCode.PROVIDER_ERROR, failure_detail=str(error))
    try:
        response = BaselineActionResponse.model_validate_json(completion.raw_response)
    except ValidationError as error:
        return BaselineRunArtifact(**common, status=BaselineRunStatus.FAILED, completed_at=clock(), attempt_count=1,
            provider=completion.provider, model=completion.model, prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens, raw_response=completion.raw_response,
            failure_code=BaselineFailureCode.MODEL_SCHEMA, failure_detail=_compact_validation_error(error))
    policy_failure = _validate_response_against_evidence(response, case_id=case_id, evidence=evidence)
    if policy_failure:
        return BaselineRunArtifact(**common, status=BaselineRunStatus.FAILED, completed_at=clock(), attempt_count=1,
            provider=completion.provider, model=completion.model, prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens, raw_response=completion.raw_response, response=response,
            failure_code=BaselineFailureCode.OUTPUT_POLICY, failure_detail=policy_failure)
    return BaselineRunArtifact(**common, status=BaselineRunStatus.COMPLETED, completed_at=clock(), attempt_count=1,
        provider=completion.provider, model=completion.model, prompt_tokens=completion.prompt_tokens,
        completion_tokens=completion.completion_tokens, raw_response=completion.raw_response, response=response)


def write_run_artifact(path, artifact: BaselineRunArtifact) -> None:
    """Write a canonical JSON artifact without embedding secrets."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")


def _validate_response_against_case(response: BaselineActionResponse, case: FrozenCaseBundle) -> str | None:
    if response.case_id != case.manifest.fixture_id:
        return "response.case_id does not match the frozen case"
    known_evidence_ids = {source.source_id for source in case.dossier.sources}
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


def _validate_response_against_evidence(
    response: BaselineActionResponse, *, case_id: str, evidence: VerifiedEvidencePackage
) -> str | None:
    if response.case_id != case_id:
        return "response.case_id does not match the saved live source case"
    known_evidence_ids = {snapshot.snapshot_id for snapshot in evidence.snapshots} | {snapshot.source_id for snapshot in evidence.snapshots}
    unknown = sorted({evidence_id for action in response.actions for evidence_id in action.evidence_ids if evidence_id not in known_evidence_ids})
    if unknown:
        return f"response references unknown evidence IDs: {unknown}"
    return None


def _compact_validation_error(error: ValidationError) -> str:
    return json.dumps(error.errors(include_url=False), separators=(",", ":"), default=str)[:2000]
