"""Explicit, leased workflow engine for baseline and future agent runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from climate_cascade.agents import ResponseSupervisorRunStatus, load_response_supervisor_config, run_response_supervisor
from climate_cascade.baseline import ModelGateway, run_baseline
from climate_cascade.domain import EvidenceStatus, RunMode, RunState, VerifiedEvidencePackage, load_frozen_case
from climate_cascade.evaluation import evaluate_agent_run, evaluate_baseline
from climate_cascade.persistence import LocalArtifactStore, RunRepository, RunSnapshot
from climate_cascade.sources import build_evidence_package_for_run


GatewayFactory = Callable[[dict[str, object]], ModelGateway | None]
EvidencePackageFactory = Callable[[RunSnapshot], VerifiedEvidencePackage]


@dataclass(frozen=True)
class WorkflowResult:
    run_id: str
    state: RunState
    claimed: bool


class WorkflowEngine:
    def __init__(
        self,
        *,
        repository: RunRepository,
        artifact_store: LocalArtifactStore,
        case_root: Path,
        gateway_factory: GatewayFactory,
        evidence_package_factory: EvidencePackageFactory | None = None,
        response_supervisor_config_path: Path | None = None,
        lease_seconds: int = 120,
    ) -> None:
        self._repository = repository
        self._artifact_store = artifact_store
        self._case_root = case_root
        self._gateway_factory = gateway_factory
        self._evidence_package_factory = evidence_package_factory or (
            lambda run: build_evidence_package_for_run(run=run, case_root=self._case_root)
        )
        self._response_supervisor_config_path = response_supervisor_config_path or Path(
            "config/agents/response_supervisor.json"
        )
        self._lease_seconds = lease_seconds

    def process_next(self, *, worker_id: str) -> WorkflowResult | None:
        run = self._repository.lease_next_run(worker_id=worker_id, lease_seconds=self._lease_seconds)
        if run is None:
            return None
        try:
            final = self._process_claimed(run, worker_id=worker_id)
            return WorkflowResult(run_id=final.run_id, state=final.state, claimed=True)
        except Exception as error:  # Preserve unexpected failures as durable blocked state.
            current = self._repository.get_run(run.run_id)
            if current.state not in {RunState.BLOCKED, RunState.REJECTED, RunState.EXPORTED, RunState.AWAITING_HUMAN_REVIEW}:
                final = self._repository.transition(
                    run.run_id,
                    worker_id=worker_id,
                    to_state=RunState.BLOCKED,
                    message=f"Workflow blocked by {type(error).__name__}: {error}",
                    event_type="workflow_failed",
                )
                return WorkflowResult(run_id=final.run_id, state=final.state, claimed=True)
            raise
        finally:
            current = self._repository.get_run(run.run_id)
            if current.lease_owner == worker_id:
                self._repository.release_lease(run.run_id, worker_id=worker_id)

    def _process_claimed(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        current = run
        if current.mode is RunMode.AGENT:
            return self._process_agent(current, worker_id=worker_id)
        while current.state not in {RunState.BLOCKED, RunState.AWAITING_HUMAN_REVIEW, RunState.REJECTED, RunState.EXPORTED}:
            self._repository.renew_lease(current.run_id, worker_id=worker_id, lease_seconds=self._lease_seconds)
            current = self._advance_baseline(current, worker_id=worker_id)
        return current

    def _process_agent(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        current = run
        while current.state not in {RunState.BLOCKED, RunState.AWAITING_HUMAN_REVIEW, RunState.REJECTED, RunState.EXPORTED}:
            self._repository.renew_lease(current.run_id, worker_id=worker_id, lease_seconds=self._lease_seconds)
            current = self._advance_agent(current, worker_id=worker_id)
        return current

    def _advance_agent(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        if run.state is RunState.RECEIVED:
            return self._repository.transition(
                run.run_id,
                worker_id=worker_id,
                to_state=RunState.SOURCE_CHECK,
                message="Agent run accepted; authoritative source intake is starting.",
            )
        if run.state is RunState.SOURCE_CHECK:
            return self._verify_agent_sources(run, worker_id=worker_id)
        if run.state is RunState.VERIFIED:
            artifact = self._repository.get_artifact(run.run_id, "source_evidence_package")
            if artifact is None:
                raise RuntimeError("source evidence package artifact is missing")
            return self._repository.transition(
                run.run_id,
                worker_id=worker_id,
                to_state=RunState.DATA_SNAPSHOT,
                message=f"Verified source evidence package pinned as artifact {artifact.sha256}.",
                event_type="source_snapshot_pinned",
            )
        if run.state is RunState.DATA_SNAPSHOT:
            return self._repository.transition(
                run.run_id,
                worker_id=worker_id,
                to_state=RunState.IMPACT_ANALYSIS,
                message="Source evidence is pinned. Iteration 1 uses this verified source picture without claiming deterministic impact analysis.",
                event_type="source_evidence_ready",
            )
        if run.state is RunState.IMPACT_ANALYSIS:
            return self._repository.transition(
                run.run_id,
                worker_id=worker_id,
                to_state=RunState.ACTION_DRAFTING,
                message="Response supervisor is preparing human-reviewable draft actions from verified source evidence.",
                event_type="response_supervisor_queued",
            )
        if run.state is RunState.ACTION_DRAFTING:
            return self._execute_response_supervisor(run, worker_id=worker_id)
        if run.state is RunState.EVIDENCE_VERIFICATION:
            return self._evaluate_response_supervisor(run, worker_id=worker_id)
        raise RuntimeError(f"agent workflow cannot advance from {run.state.value}")

    def _verify_agent_sources(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        self._repository.record_progress(
            run.run_id,
            worker_id=worker_id,
            event_type="source_intake_started",
            message="Working: retrieving and checking authoritative source snapshots before drafting any response.",
        )
        package = self._evidence_package_factory(run)
        stored = self._artifact_store.put_json(package.model_dump(mode="json"))
        self._repository.store_artifact(run.run_id, logical_name="source_evidence_package", artifact=stored)
        evidence_ids = tuple(claim.claim_id for claim in package.claims)
        if package.verification_status is EvidenceStatus.CONFLICTING:
            return self._repository.transition(
                run.run_id,
                worker_id=worker_id,
                to_state=RunState.BLOCKED,
                message="Source verification blocked because the source package conflicts with MVP policy.",
                evidence_ids=evidence_ids,
                event_type="source_verification_blocked",
            )
        return self._repository.transition(
            run.run_id,
            worker_id=worker_id,
            to_state=RunState.VERIFIED,
            message=(
                f"Source verification produced a {package.verification_status.value} evidence package "
                f"with {len(package.snapshots)} snapshot(s), {len(package.claims)} claim(s), "
                f"and {len(package.data_gaps)} data gap(s)."
            ),
            evidence_ids=evidence_ids,
            event_type="source_verified",
        )

    def _execute_response_supervisor(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        evidence = self._load_evidence_package(run.run_id)
        case = load_frozen_case(self._case_root / run.case_id) if run.fixture_mode else None
        config = load_response_supervisor_config(self._response_supervisor_config_path)
        self._repository.record_progress(
            run.run_id,
            worker_id=worker_id,
            event_type="response_supervisor_started",
            message=(
                "Working: the response supervisor is generating a constrained structured draft from saved evidence. "
                "Private model reasoning is not displayed."
            ),
        )
        artifact = run_response_supervisor(
            run_id=run.run_id,
            case_id=run.case_id,
            evidence=evidence,
            config=config,
            gateway=self._gateway_factory(run.config),
            case=case,
        )
        stored = self._artifact_store.put_json(artifact.model_dump(mode="json"))
        self._repository.store_artifact(run.run_id, logical_name="response_supervisor_run", artifact=stored)
        self._repository.record_progress(
            run.run_id,
            worker_id=worker_id,
            event_type="response_supervisor_response_received",
            message=(
                "Structured response received and saved. The workflow is applying the output contract before "
                "showing any draft to a reviewer."
            ),
        )
        if artifact.status is not ResponseSupervisorRunStatus.COMPLETED:
            return self._repository.transition(
                run.run_id,
                worker_id=worker_id,
                to_state=RunState.BLOCKED,
                message=f"Response supervisor failed with {artifact.failure_code}; inspect its immutable run artifact.",
                event_type="response_supervisor_failed",
            )
        assert artifact.response is not None
        return self._repository.transition(
            run.run_id,
            worker_id=worker_id,
            to_state=RunState.EVIDENCE_VERIFICATION,
            message=(
                f"Response supervisor stored {len(artifact.response.actions)} draft action(s); "
                "deterministic evidence and safety checks are running."
            ),
            evidence_ids=tuple(
                sorted({evidence_id for action in artifact.response.actions for evidence_id in action.evidence_ids})
            ),
            event_type="response_supervisor_completed",
        )

    def _evaluate_response_supervisor(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        from climate_cascade.agents import ResponseSupervisorRunArtifact

        evidence = self._load_evidence_package(run.run_id)
        stored_run = self._repository.get_artifact(run.run_id, "response_supervisor_run")
        if stored_run is None:
            raise RuntimeError("response supervisor run artifact is missing")
        supervisor_run = ResponseSupervisorRunArtifact.model_validate_json(stored_run.storage_path.read_text(encoding="utf-8"))
        case = load_frozen_case(self._case_root / run.case_id) if run.fixture_mode else None
        self._repository.record_progress(
            run.run_id,
            worker_id=worker_id,
            event_type="draft_checks_started",
            message="Analyzing: deterministic safety and evidence-reference checks are running on the saved draft.",
        )
        report = evaluate_agent_run(run=supervisor_run, evidence=evidence, case=case)
        stored_report = self._artifact_store.put_json(report.model_dump(mode="json"))
        self._repository.store_artifact(run.run_id, logical_name="agent_evaluation", artifact=stored_report)
        return self._repository.transition(
            run.run_id,
            worker_id=worker_id,
            to_state=RunState.AWAITING_HUMAN_REVIEW,
            message=(
                "Draft actions passed deterministic evidence and safety checks; "
                "a qualified human must adjudicate coverage before LSAC@5 is reported."
            ),
            event_type="agent_evaluation_completed",
        )

    def _load_evidence_package(self, run_id: str) -> VerifiedEvidencePackage:
        stored = self._repository.get_artifact(run_id, "source_evidence_package")
        if stored is None:
            raise RuntimeError("source evidence package artifact is missing")
        return VerifiedEvidencePackage.model_validate_json(stored.storage_path.read_text(encoding="utf-8"))

    def _advance_baseline(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        transitions = {
            RunState.RECEIVED: (RunState.SOURCE_CHECK, "Frozen fixture queued for integrity-checked source review."),
            RunState.SOURCE_CHECK: (RunState.VERIFIED, "Frozen fixture source references accepted for baseline execution."),
            RunState.VERIFIED: (RunState.DATA_SNAPSHOT, "Baseline uses the pinned fixture as its immutable data snapshot."),
            RunState.DATA_SNAPSHOT: (RunState.IMPACT_ANALYSIS, "Baseline has no deterministic impact tool; curated impact summary remains visible."),
            RunState.IMPACT_ANALYSIS: (RunState.ACTION_DRAFTING, "Baseline action drafting is ready for its one structured model call."),
        }
        if run.state in transitions:
            target, message = transitions[run.state]
            return self._repository.transition(run.run_id, worker_id=worker_id, to_state=target, message=message)
        if run.state is RunState.ACTION_DRAFTING:
            return self._execute_baseline(run, worker_id=worker_id)
        if run.state is RunState.EVIDENCE_VERIFICATION:
            return self._write_baseline_evaluation(run, worker_id=worker_id)
        raise RuntimeError(f"baseline cannot advance from {run.state.value}")

    def _execute_baseline(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        case = load_frozen_case(self._case_root / run.case_id)
        artifact = run_baseline(case, self._gateway_factory(run.config))
        stored = self._artifact_store.put_json(artifact.model_dump(mode="json"))
        self._repository.store_artifact(run.run_id, logical_name="baseline_run", artifact=stored)
        if artifact.status.value != "completed":
            report = evaluate_baseline(case, artifact)
            report_artifact = self._artifact_store.put_json(report.model_dump(mode="json"))
            self._repository.store_artifact(run.run_id, logical_name="baseline_evaluation", artifact=report_artifact)
            return self._repository.transition(
                run.run_id,
                worker_id=worker_id,
                to_state=RunState.BLOCKED,
                message=f"Baseline model call failed with {artifact.failure_code}; inspect immutable artifacts before creating a new run.",
                event_type="baseline_failed",
            )
        return self._repository.transition(
            run.run_id,
            worker_id=worker_id,
            to_state=RunState.EVIDENCE_VERIFICATION,
            message="One baseline model response was stored; deterministic validation is running.",
            event_type="baseline_completed",
        )

    def _write_baseline_evaluation(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        case = load_frozen_case(self._case_root / run.case_id)
        stored_run = self._repository.get_artifact(run.run_id, "baseline_run")
        if stored_run is None:
            raise RuntimeError("baseline run artifact is missing")
        from climate_cascade.baseline.runner import BaselineRunArtifact

        baseline_run = BaselineRunArtifact.model_validate_json(stored_run.storage_path.read_text(encoding="utf-8"))
        report = evaluate_baseline(case, baseline_run)
        stored_report = self._artifact_store.put_json(report.model_dump(mode="json"))
        self._repository.store_artifact(run.run_id, logical_name="baseline_evaluation", artifact=stored_report)
        return self._repository.transition(
            run.run_id,
            worker_id=worker_id,
            to_state=RunState.AWAITING_HUMAN_REVIEW,
            message="Deterministic baseline checks completed; human coverage adjudication is required for LSAC@5.",
            event_type="baseline_evaluated",
        )
