"""Explicit, leased workflow engine for baseline and future agent runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from climate_cascade.baseline import ModelGateway, run_baseline
from climate_cascade.domain import EvidenceStatus, RunMode, RunState, VerifiedEvidencePackage, load_frozen_case
from climate_cascade.evaluation import evaluate_baseline
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
        lease_seconds: int = 120,
    ) -> None:
        self._repository = repository
        self._artifact_store = artifact_store
        self._case_root = case_root
        self._gateway_factory = gateway_factory
        self._evidence_package_factory = evidence_package_factory or (
            lambda run: build_evidence_package_for_run(run=run, case_root=self._case_root)
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
            return self._process_agent_source_intake(current, worker_id=worker_id)
        while current.state not in {RunState.BLOCKED, RunState.AWAITING_HUMAN_REVIEW, RunState.REJECTED, RunState.EXPORTED}:
            self._repository.renew_lease(current.run_id, worker_id=worker_id, lease_seconds=self._lease_seconds)
            current = self._advance_baseline(current, worker_id=worker_id)
        return current

    def _process_agent_source_intake(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
        current = run
        while current.state not in {RunState.BLOCKED, RunState.AWAITING_HUMAN_REVIEW, RunState.REJECTED, RunState.EXPORTED}:
            self._repository.renew_lease(current.run_id, worker_id=worker_id, lease_seconds=self._lease_seconds)
            current = self._advance_agent_source_intake(current, worker_id=worker_id)
        return current

    def _advance_agent_source_intake(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
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
                to_state=RunState.BLOCKED,
                message="Iteration 1 source intake is complete; deterministic impact analysis is pending ADR step 7.",
                event_type="impact_analysis_pending",
            )
        raise RuntimeError(f"agent source intake cannot advance from {run.state.value}")

    def _verify_agent_sources(self, run: RunSnapshot, *, worker_id: str) -> RunSnapshot:
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
