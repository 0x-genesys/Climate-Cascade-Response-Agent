"""Stable, versioned contracts shared by the baseline and later agent workflow."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

SCHEMA_VERSION = "1"

Identifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=96,
        pattern=r"^[a-z][a-z0-9_-]*$",
    ),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictModel(BaseModel):
    """Reject unknown fields so fixture and tool contracts cannot silently drift."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RunMode(StrEnum):
    BASELINE = "baseline"
    AGENT = "agent"


class HazardType(StrEnum):
    FLOOD_DEBRIS_FLOW = "flood_debris_flow"
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    TORNADO = "tornado"
    VOLCANIC_ERUPTION = "volcanic_eruption"


class EvidenceStatus(StrEnum):
    SUPPORTED = "supported"
    PRELIMINARY = "preliminary"
    CONFLICTING = "conflicting"
    UNKNOWN = "unknown"


class SourceSnapshotKind(StrEnum):
    CURATED_FIXTURE = "curated_fixture"
    RAW_HTTP_JSON = "raw_http_json"


class SourceVerificationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class RunState(StrEnum):
    RECEIVED = "received"
    SOURCE_CHECK = "source_check"
    VERIFIED = "verified"
    BLOCKED = "blocked"
    DATA_SNAPSHOT = "data_snapshot"
    IMPACT_ANALYSIS = "impact_analysis"
    ACTION_DRAFTING = "action_drafting"
    EVIDENCE_VERIFICATION = "evidence_verification"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    REJECTED = "rejected"
    EXPORTED = "exported"


class ActionUrgency(StrEnum):
    IMMEDIATE = "immediate"
    UNDER_SIX_HOURS = "under_six_hours"
    UNDER_TWENTY_FOUR_HOURS = "under_twenty_four_hours"
    MONITOR = "monitor"


class ActionStatus(StrEnum):
    DRAFT = "draft"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewDecisionType(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"
    REQUEST_EVIDENCE = "request_evidence"
    REJECT = "reject"


class LifeSafetyStatus(StrEnum):
    ESTIMATED = "estimated"
    NOT_ESTIMABLE = "not_estimable"


def _require_timezone(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value


class SourceReference(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    source_id: Identifier
    publisher: NonEmptyText
    source_url: Annotated[str, StringConstraints(pattern=r"^https://")]
    retrieved_at: datetime
    materialization: Literal["curated_summary", "raw_snapshot"]
    upstream_sha256: Sha256 | None = None
    license_note: NonEmptyText

    _retrieved_at_timezone = field_validator("retrieved_at")(_require_timezone)


class EvidenceClaim(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    claim_id: Identifier
    statement: NonEmptyText
    status: EvidenceStatus
    source_ids: list[Identifier] = Field(min_length=1)


class EventInput(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    event_id: Identifier
    display_name: NonEmptyText
    hazard_type: HazardType
    occurred_at: datetime
    location_summary: NonEmptyText
    activation_code: Identifier | None = None

    _occurred_at_timezone = field_validator("occurred_at")(_require_timezone)


class ImpactSummary(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    analysis_status: Literal["curated_source_summary", "deterministic_analysis"]
    affected_population: int = Field(ge=0)
    affected_buildings: int = Field(ge=0)
    affected_roads_km: float = Field(ge=0)
    affected_bridge_features: int = Field(ge=0)
    source_ids: list[Identifier] = Field(min_length=1)
    note: NonEmptyText


class IncidentDossier(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    case_id: Identifier
    title: NonEmptyText
    event: EventInput
    sources: list[SourceReference] = Field(min_length=1)
    claims: list[EvidenceClaim] = Field(min_length=1)
    impact_summary: ImpactSummary
    data_gaps: list[NonEmptyText]
    safety_note: NonEmptyText

    @model_validator(mode="after")
    def unique_source_and_claim_ids(self) -> "IncidentDossier":
        source_ids = [source.source_id for source in self.sources]
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("sources must use unique source_id values")
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("claims must use unique claim_id values")
        source_id_set = set(source_ids)
        for claim in self.claims:
            unknown = set(claim.source_ids) - source_id_set
            if unknown:
                raise ValueError(f"claim {claim.claim_id} references unknown sources: {sorted(unknown)}")
        if not set(self.impact_summary.source_ids).issubset(source_id_set):
            raise ValueError("impact_summary references an unknown source")
        return self


class OperationalConstraint(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    constraint_id: Identifier
    description: NonEmptyText
    origin: Literal["synthetic", "source"]
    source_ids: list[Identifier] = Field(default_factory=list)

    @model_validator(mode="after")
    def source_origin_is_explicit(self) -> "OperationalConstraint":
        if self.origin == "synthetic" and self.source_ids:
            raise ValueError("synthetic constraints cannot cite external source IDs")
        if self.origin == "source" and not self.source_ids:
            raise ValueError("source constraints require source IDs")
        return self


class OperationalScenario(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    scenario_id: Identifier
    case_id: Identifier
    is_synthetic_overlay: Literal[True] = True
    constraints: list[OperationalConstraint] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_constraint_ids(self) -> "OperationalScenario":
        constraint_ids = [constraint.constraint_id for constraint in self.constraints]
        if len(constraint_ids) != len(set(constraint_ids)):
            raise ValueError("constraints must use unique constraint_id values")
        return self


class GoldAction(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    gold_action_id: Identifier
    required_outcome: NonEmptyText
    location_ref: NonEmptyText
    owner_role: NonEmptyText
    urgency: ActionUrgency
    severity_weight: int = Field(ge=1, le=5)
    source_ids: list[Identifier] = Field(min_length=1)
    constraint_ids: list[Identifier] = Field(default_factory=list)


class GoldActionSet(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    case_id: Identifier
    actions: list[GoldAction] = Field(min_length=1)
    forbidden_action_patterns: list[NonEmptyText] = Field(min_length=1)
    provenance_note: NonEmptyText

    @model_validator(mode="after")
    def unique_gold_action_ids(self) -> "GoldActionSet":
        action_ids = [action.gold_action_id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("gold actions must use unique gold_action_id values")
        return self


class FrozenArtifact(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    relative_path: NonEmptyText
    sha256: Sha256

    @field_validator("relative_path")
    @classmethod
    def relative_path_stays_inside_case(cls, value: str) -> str:
        if value.startswith("/") or ".." in value.split("/"):
            raise ValueError("artifact path must remain inside the case directory")
        return value


class FrozenCaseManifest(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    fixture_id: Identifier
    fixture_version: int = Field(ge=1)
    frozen_at: datetime
    run_mode: Literal[RunMode.BASELINE] = RunMode.BASELINE
    hazard_type: HazardType
    data_classification: Literal["public_cited_plus_synthetic_constraints"]
    dossier_path: NonEmptyText
    scenario_path: NonEmptyText
    gold_actions_path: NonEmptyText
    artifacts: list[FrozenArtifact] = Field(min_length=3)

    _frozen_at_timezone = field_validator("frozen_at")(_require_timezone)

    @model_validator(mode="after")
    def manifest_paths_are_listed_once(self) -> "FrozenCaseManifest":
        artifact_paths = [artifact.relative_path for artifact in self.artifacts]
        required_paths = {self.dossier_path, self.scenario_path, self.gold_actions_path}
        if len(artifact_paths) != len(set(artifact_paths)):
            raise ValueError("artifacts must use unique paths")
        if not required_paths.issubset(set(artifact_paths)):
            raise ValueError("required case files must be integrity-protected artifacts")
        return self


class FrozenCaseBundle(StrictModel):
    manifest: FrozenCaseManifest
    dossier: IncidentDossier
    scenario: OperationalScenario
    gold_actions: GoldActionSet


class SourceSnapshot(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    snapshot_id: Identifier
    source_id: Identifier
    adapter: Identifier
    publisher: NonEmptyText
    source_url: Annotated[str, StringConstraints(pattern=r"^https://")]
    retrieved_at: datetime
    kind: SourceSnapshotKind
    content_sha256: Sha256
    content_type: NonEmptyText
    license_note: NonEmptyText
    raw_content: dict[str, Any] | None = None

    _retrieved_at_timezone = field_validator("retrieved_at")(_require_timezone)


class CemsAoiProductStatus(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    aoi_number: int = Field(ge=1)
    aoi_name: NonEmptyText
    product_type: NonEmptyText
    feasible: bool | None = None
    status_code: NonEmptyText
    status_label: NonEmptyText
    delivery_time: NonEmptyText | None = None
    expected_delivery: NonEmptyText | None = None
    download_path: Annotated[str, StringConstraints(pattern=r"^https://")] | None = None


class CemsActivationSummary(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    activation_code: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^EMSR[0-9]{3}$")]
    name: NonEmptyText
    category: NonEmptyText
    sub_category: NonEmptyText | None = None
    event_time: NonEmptyText | None = None
    activation_time: NonEmptyText | None = None
    countries: list[NonEmptyText] = Field(default_factory=list)
    closed: bool
    report_link: Annotated[str, StringConstraints(pattern=r"^https://")] | None = None
    products_path: Annotated[str, StringConstraints(pattern=r"^https://")] | None = None
    charter_number: NonEmptyText | None = None
    charter_url: Annotated[str, StringConstraints(pattern=r"^https://")] | None = None
    stats: dict[str, str | int | float | bool] = Field(default_factory=dict)
    aois: list[CemsAoiProductStatus] = Field(default_factory=list)

    @property
    def finished_product_count(self) -> int:
        return sum(1 for aoi in self.aois if aoi.status_code.upper() == "F")

    @property
    def pending_product_count(self) -> int:
        return sum(1 for aoi in self.aois if aoi.status_code.upper() in {"W", "I"})


class SourceVerificationFinding(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    finding_id: Identifier
    severity: SourceVerificationSeverity
    status: EvidenceStatus
    message: NonEmptyText
    source_ids: list[Identifier] = Field(min_length=1)


class VerifiedEvidencePackage(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    package_id: Identifier
    case_id: Identifier
    activation_code: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^EMSR[0-9]{3}$")]
    hazard_type: HazardType
    verification_status: EvidenceStatus
    retrieved_at: datetime
    snapshots: list[SourceSnapshot] = Field(min_length=1)
    claims: list[EvidenceClaim] = Field(min_length=1)
    findings: list[SourceVerificationFinding] = Field(min_length=1)
    data_gaps: list[NonEmptyText] = Field(default_factory=list)
    cems_activation: CemsActivationSummary | None = None

    _retrieved_at_timezone = field_validator("retrieved_at")(_require_timezone)

    @model_validator(mode="after")
    def source_references_are_known(self) -> "VerifiedEvidencePackage":
        source_ids = [snapshot.source_id for snapshot in self.snapshots]
        claim_ids = [claim.claim_id for claim in self.claims]
        finding_ids = [finding.finding_id for finding in self.findings]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("snapshots must use unique source_id values")
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("claims must use unique claim_id values")
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError("findings must use unique finding_id values")
        known_sources = set(source_ids)
        for claim in self.claims:
            unknown = set(claim.source_ids) - known_sources
            if unknown:
                raise ValueError(f"claim {claim.claim_id} references unknown sources: {sorted(unknown)}")
        for finding in self.findings:
            unknown = set(finding.source_ids) - known_sources
            if unknown:
                raise ValueError(f"finding {finding.finding_id} references unknown sources: {sorted(unknown)}")
        return self


class ImpactAnalysisStatus(StrEnum):
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"


class PopulationImpact(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    affected_population: int | None = Field(default=None, ge=0)
    source_label: NonEmptyText
    deduplication_group: Identifier
    evidence_ids: list[Identifier] = Field(min_length=1)


class AssetImpact(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    asset_class: NonEmptyText
    affected_value: float = Field(ge=0)
    unit: NonEmptyText
    evidence_ids: list[Identifier] = Field(min_length=1)


class AccessImpact(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    affected_road_km: float = Field(ge=0)
    affected_bridge_features: int = Field(ge=0)
    status: Literal["needs_human_verification", "not_indicated", "unknown"]
    evidence_ids: list[Identifier] = Field(min_length=1)


class AoiImpact(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    aoi_number: int = Field(ge=1)
    aoi_name: NonEmptyText
    product_type: NonEmptyText
    product_delivery_time: NonEmptyText | None = None
    population: PopulationImpact | None = None
    affected_residential_buildings: int | None = Field(default=None, ge=0)
    assets: list[AssetImpact] = Field(default_factory=list)
    access: AccessImpact
    evidence_ids: list[Identifier] = Field(min_length=1)


class ImpactPackage(StrictModel):
    """Deterministic, compact CEMS product-statistics analysis for one run."""

    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    package_id: Identifier
    run_id: str = Field(pattern=r"^run-[a-f0-9-]{36}$")
    source_package_id: Identifier
    analysis_version: Literal["cems-product-stats-v1"]
    status: ImpactAnalysisStatus
    analyzed_at: datetime
    aoi_impacts: list[AoiImpact] = Field(default_factory=list)
    data_gaps: list[NonEmptyText] = Field(default_factory=list)
    deduplication_note: NonEmptyText

    _analyzed_at_timezone = field_validator("analyzed_at")(_require_timezone)


class LifeSafetyEstimate(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    action_id: Identifier
    status: LifeSafetyStatus
    low: float | None = Field(default=None, ge=0)
    central: float | None = Field(default=None, ge=0)
    high: float | None = Field(default=None, ge=0)
    parameter_set_id: Identifier | None = None
    population_deduplication_group: Identifier | None = None
    abstention_reason: NonEmptyText | None = None

    @model_validator(mode="after")
    def estimate_or_abstention_is_complete(self) -> "LifeSafetyEstimate":
        values = (self.low, self.central, self.high)
        if self.status == LifeSafetyStatus.ESTIMATED:
            if any(value is None for value in values):
                raise ValueError("estimated life-safety values require low, central, and high")
            if self.low > self.central or self.central > self.high:
                raise ValueError("life-safety range must satisfy low <= central <= high")
            if not self.parameter_set_id or not self.population_deduplication_group:
                raise ValueError("estimated values require parameter and deduplication references")
            if self.abstention_reason is not None:
                raise ValueError("estimated values cannot include an abstention reason")
        else:
            if any(value is not None for value in values):
                raise ValueError("not estimable values cannot include numeric estimates")
            if not self.abstention_reason:
                raise ValueError("not estimable values require a reason")
        return self


class NotEstimableLifeSafetyEstimate(LifeSafetyEstimate):
    """Iteration 1 may explain an abstention but cannot produce numeric estimates."""

    status: Literal[LifeSafetyStatus.NOT_ESTIMABLE] = LifeSafetyStatus.NOT_ESTIMABLE


class ActionCandidate(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    action_id: Identifier
    title: NonEmptyText
    location_ref: NonEmptyText
    owner_role: NonEmptyText
    urgency: ActionUrgency
    evidence_ids: list[Identifier] = Field(min_length=1)
    status: ActionStatus = ActionStatus.DRAFT
    estimate: LifeSafetyEstimate | None = None

    @model_validator(mode="after")
    def estimate_belongs_to_action(self) -> "ActionCandidate":
        if self.estimate and self.estimate.action_id != self.action_id:
            raise ValueError("estimate.action_id must match action_id")
        return self


class ResponseSupervisorActionCandidate(StrictModel):
    """Draft action shape for the response supervisor before the estimator is implemented."""

    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    action_id: Identifier
    title: NonEmptyText
    location_ref: NonEmptyText
    owner_role: NonEmptyText
    urgency: ActionUrgency
    evidence_ids: list[Identifier] = Field(min_length=1)
    status: ActionStatus = ActionStatus.DRAFT
    estimate: NotEstimableLifeSafetyEstimate | None = None

    @model_validator(mode="after")
    def estimate_belongs_to_action(self) -> "ResponseSupervisorActionCandidate":
        if self.estimate and self.estimate.action_id != self.action_id:
            raise ValueError("estimate.action_id must match action_id")
        if self.status is not ActionStatus.DRAFT:
            raise ValueError("response supervisor actions must remain drafts")
        return self


class BaselineActionResponse(StrictModel):
    """The one-call baseline response, intentionally limited to draft actions."""

    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    case_id: Identifier
    actions: list[ActionCandidate] = Field(min_length=1, max_length=5)
    limitations: list[NonEmptyText] = Field(min_length=1)

    @model_validator(mode="after")
    def actions_are_unique_unestimated_drafts(self) -> "BaselineActionResponse":
        action_ids = [action.action_id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("baseline actions must use unique action_id values")
        if any(action.status is not ActionStatus.DRAFT for action in self.actions):
            raise ValueError("baseline actions must remain drafts")
        if any(action.estimate is not None for action in self.actions):
            raise ValueError("baseline cannot produce life-safety estimates")
        return self


class ResponseSupervisorActionResponse(StrictModel):
    """One bounded supervisor response with safe life-safety abstentions only."""

    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    case_id: Identifier
    actions: list[ResponseSupervisorActionCandidate] = Field(min_length=1, max_length=5)
    limitations: list[NonEmptyText] = Field(min_length=1)

    @model_validator(mode="after")
    def action_ids_are_unique(self) -> "ResponseSupervisorActionResponse":
        action_ids = [action.action_id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("response supervisor actions must use unique action_id values")
        return self


class ReviewDecision(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    action_id: Identifier
    decision: ReviewDecisionType
    reviewer_id: Identifier
    reviewer_role: NonEmptyText
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10)]
    decided_at: datetime

    _decided_at_timezone = field_validator("decided_at")(_require_timezone)


class ProgressEvent(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    event_id: Identifier
    run_id: Identifier
    sequence: int = Field(ge=1)
    state: RunState
    message: NonEmptyText
    created_at: datetime

    _created_at_timezone = field_validator("created_at")(_require_timezone)
