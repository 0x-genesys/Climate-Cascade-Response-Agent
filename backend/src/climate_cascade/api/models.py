"""HTTP contracts for the local control API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated

from climate_cascade.domain import Identifier, RunMode, RunState


IdempotencyKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=8, max_length=128)]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateRunRequest(ApiModel):
    case_id: Identifier
    mode: RunMode
    fixture_mode: bool = True
    activation: str | None = None
    secondary_source_url: str | None = None
    operational_constraints: list[str] = Field(default_factory=list)
    model: str | None = None
    api_key_env: str = "OPENAI_API_KEY"

    @model_validator(mode="after")
    def live_agent_runs_require_activation(self) -> "CreateRunRequest":
        if self.mode is RunMode.AGENT and not self.fixture_mode and not self.activation:
            raise ValueError("live agent runs require an activation code")
        if self.mode is RunMode.AGENT and not self.model:
            raise ValueError("agent runs require a structured-output model identifier")
        return self


class CreateBaselineRunRequest(ApiModel):
    case_id: Identifier
    fixture_mode: Literal[True] = True
    model: str
    api_key_env: str = "OPENAI_API_KEY"


class RunResponse(ApiModel):
    run_id: str
    case_id: str
    mode: RunMode
    state: RunState
    fixture_mode: bool
    stage_attempt: int
    lease_owner: str | None
    lease_expires_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RunListResponse(ApiModel):
    runs: list[RunResponse]


class ErrorDetail(ApiModel):
    code: str
    message: str
    retryable: bool
    details: dict[str, object] = Field(default_factory=dict)
    correlation_id: str


class ErrorEnvelope(ApiModel):
    error: ErrorDetail
