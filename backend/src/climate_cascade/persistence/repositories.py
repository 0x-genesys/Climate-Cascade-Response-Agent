"""Repositories that enforce durable workflow, event, and lease semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from climate_cascade.domain import RunMode, RunState

from .artifacts import StoredArtifact
from .schema import ActionReviewRecord, ArtifactRecord, RunArtifactRecord, RunEventRecord, RunRecord


ACTIVE_STATES = {
    RunState.RECEIVED,
    RunState.SOURCE_CHECK,
    RunState.VERIFIED,
    RunState.DATA_SNAPSHOT,
    RunState.IMPACT_ANALYSIS,
    RunState.ACTION_DRAFTING,
    RunState.EVIDENCE_VERIFICATION,
    RunState.REVISION_REQUESTED,
}
TERMINAL_STATES = {RunState.BLOCKED, RunState.REJECTED, RunState.EXPORTED}
ALLOWED_TRANSITIONS = {
    RunState.RECEIVED: {RunState.SOURCE_CHECK, RunState.BLOCKED},
    RunState.SOURCE_CHECK: {RunState.VERIFIED, RunState.BLOCKED},
    RunState.VERIFIED: {RunState.DATA_SNAPSHOT, RunState.BLOCKED},
    RunState.DATA_SNAPSHOT: {RunState.IMPACT_ANALYSIS, RunState.BLOCKED},
    RunState.IMPACT_ANALYSIS: {RunState.ACTION_DRAFTING, RunState.BLOCKED},
    RunState.ACTION_DRAFTING: {RunState.EVIDENCE_VERIFICATION, RunState.BLOCKED},
    RunState.EVIDENCE_VERIFICATION: {RunState.AWAITING_HUMAN_REVIEW, RunState.BLOCKED},
    RunState.AWAITING_HUMAN_REVIEW: {RunState.APPROVED, RunState.REVISION_REQUESTED, RunState.REJECTED},
    RunState.APPROVED: {RunState.EXPORTED},
    RunState.REVISION_REQUESTED: {RunState.ACTION_DRAFTING, RunState.BLOCKED},
    RunState.BLOCKED: set(),
    RunState.REJECTED: set(),
    RunState.EXPORTED: set(),
}


class UnknownRunError(KeyError):
    pass


class InvalidTransitionError(ValueError):
    pass


class LeaseOwnershipError(ValueError):
    pass


@dataclass(frozen=True)
class RunSnapshot:
    run_id: str
    case_id: str
    mode: RunMode
    state: RunState
    fixture_mode: bool
    config: dict[str, object]
    config_hash: str
    stage_attempt: int
    lease_owner: str | None
    lease_expires_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RunEvent:
    sequence: int
    event_type: str
    stage: RunState
    status: str
    message: str
    evidence_ids: tuple[str, ...]
    retry_count: int
    created_at: datetime


@dataclass(frozen=True)
class ActionReview:
    action_id: str
    version: int
    decision: str
    reviewer_id: str
    reviewer_role: str
    rationale: str
    assumptions: dict[str, object]
    created_at: datetime


class RunRepository:
    def __init__(self, engine: Engine) -> None:
        self._sessions = sessionmaker(engine, expire_on_commit=False, future=True)

    def create_run(
        self,
        *,
        case_id: str,
        mode: RunMode,
        fixture_mode: bool,
        config: dict[str, object],
        idempotency_key: str,
    ) -> tuple[RunSnapshot, bool]:
        now = _now()
        config_json = _canonical_json(config)
        config_hash = sha256(config_json.encode("utf-8")).hexdigest()
        with self._sessions.begin() as session:
            existing = session.scalar(select(RunRecord).where(RunRecord.idempotency_key == idempotency_key))
            if existing is not None:
                if existing.case_id != case_id or existing.mode != mode.value or existing.config_hash != config_hash:
                    raise ValueError("idempotency key was already used with a different run request")
                return _snapshot(existing), False
            record = RunRecord(
                run_id=f"run-{uuid4()}",
                idempotency_key=idempotency_key,
                case_id=case_id,
                mode=mode.value,
                state=RunState.RECEIVED.value,
                fixture_mode=fixture_mode,
                config_json=config_json,
                config_hash=config_hash,
                stage_attempt=0,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            self._append_event(
                session,
                record,
                event_type="run_created",
                status="queued",
                message="Run was accepted and queued for a worker lease.",
            )
            return _snapshot(record), True

    def get_run(self, run_id: str) -> RunSnapshot:
        with self._sessions() as session:
            record = session.get(RunRecord, run_id)
            if record is None:
                raise UnknownRunError(run_id)
            return _snapshot(record)

    def list_runs(self, *, limit: int = 25) -> list[RunSnapshot]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._sessions() as session:
            rows = session.scalars(select(RunRecord).order_by(RunRecord.created_at.desc()).limit(limit)).all()
            return [_snapshot(row) for row in rows]

    def list_events(self, run_id: str, *, after_sequence: int = 0) -> list[RunEvent]:
        with self._sessions() as session:
            rows = session.scalars(
                select(RunEventRecord)
                .where(RunEventRecord.run_id == run_id, RunEventRecord.sequence > after_sequence)
                .order_by(RunEventRecord.sequence)
            ).all()
            return [_event(row) for row in rows]

    def lease_next_run(self, *, worker_id: str, lease_seconds: int) -> RunSnapshot | None:
        now = _now()
        expiry = now + timedelta(seconds=lease_seconds)
        with self._sessions() as session:
            # SQLite has no row-level locks. BEGIN IMMEDIATE serializes competing lease claims.
            session.execute(text("BEGIN IMMEDIATE"))
            record = session.scalar(
                select(RunRecord)
                .where(
                    RunRecord.state.in_([state.value for state in ACTIVE_STATES]),
                    (RunRecord.lease_expires_at.is_(None)) | (RunRecord.lease_expires_at < now),
                )
                .order_by(RunRecord.created_at)
                .limit(1)
            )
            if record is None:
                session.commit()
                return None
            record.lease_owner = worker_id
            record.lease_expires_at = expiry
            record.started_at = record.started_at or now
            record.updated_at = now
            self._append_event(
                session,
                record,
                event_type="lease_acquired",
                status="leased",
                message=f"Run leased by worker {worker_id} until {expiry.isoformat()}.",
            )
            snapshot = _snapshot(record)
            session.commit()
            return snapshot

    def renew_lease(self, run_id: str, *, worker_id: str, lease_seconds: int) -> RunSnapshot:
        with self._sessions.begin() as session:
            record = self._require_owned_run(session, run_id, worker_id)
            record.lease_expires_at = _now() + timedelta(seconds=lease_seconds)
            record.updated_at = _now()
            return _snapshot(record)

    def release_lease(self, run_id: str, *, worker_id: str) -> None:
        with self._sessions.begin() as session:
            record = self._require_owned_run(session, run_id, worker_id)
            record.lease_owner = None
            record.lease_expires_at = None
            record.updated_at = _now()
            self._append_event(
                session,
                record,
                event_type="lease_released",
                status="released",
                message=f"Worker {worker_id} released the run lease.",
            )

    def transition(
        self,
        run_id: str,
        *,
        worker_id: str,
        to_state: RunState,
        message: str,
        evidence_ids: tuple[str, ...] = (),
        event_type: str = "state_transition",
        retry_count: int = 0,
    ) -> RunSnapshot:
        with self._sessions.begin() as session:
            record = self._require_owned_run(session, run_id, worker_id)
            from_state = RunState(record.state)
            if to_state not in ALLOWED_TRANSITIONS[from_state]:
                raise InvalidTransitionError(f"{from_state.value} cannot transition to {to_state.value}")
            now = _now()
            record.state = to_state.value
            record.stage_attempt += 1
            record.updated_at = now
            if to_state in TERMINAL_STATES:
                record.completed_at = now
            self._append_event(
                session,
                record,
                event_type=event_type,
                status="completed",
                message=message,
                evidence_ids=evidence_ids,
                retry_count=retry_count,
            )
            return _snapshot(record)

    def record_progress(
        self,
        run_id: str,
        *,
        worker_id: str,
        event_type: str,
        message: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> None:
        """Append an observable in-stage update without changing workflow state."""

        with self._sessions.begin() as session:
            record = self._require_owned_run(session, run_id, worker_id)
            self._append_event(
                session,
                record,
                event_type=event_type,
                status="working",
                message=message,
                evidence_ids=evidence_ids,
            )

    def store_artifact(self, run_id: str, *, logical_name: str, artifact: StoredArtifact) -> None:
        with self._sessions.begin() as session:
            record = session.get(RunRecord, run_id)
            if record is None:
                raise UnknownRunError(run_id)
            artifact_record = session.get(ArtifactRecord, artifact.sha256)
            if artifact_record is None:
                session.add(
                    ArtifactRecord(
                        sha256=artifact.sha256,
                        content_type=artifact.content_type,
                        byte_size=artifact.byte_size,
                        storage_path=str(artifact.storage_path),
                        created_at=_now(),
                    )
                )
            mapping = session.scalar(
                select(RunArtifactRecord).where(
                    RunArtifactRecord.run_id == run_id, RunArtifactRecord.logical_name == logical_name
                )
            )
            if mapping is None:
                session.add(
                    RunArtifactRecord(
                        run_id=run_id,
                        logical_name=logical_name,
                        artifact_sha256=artifact.sha256,
                        created_at=_now(),
                    )
                )
            elif mapping.artifact_sha256 != artifact.sha256:
                raise ValueError(f"logical artifact {logical_name} is immutable once stored")

    def get_artifact(self, run_id: str, logical_name: str) -> StoredArtifact | None:
        with self._sessions() as session:
            mapping = session.scalar(
                select(RunArtifactRecord).where(
                    RunArtifactRecord.run_id == run_id, RunArtifactRecord.logical_name == logical_name
                )
            )
            if mapping is None:
                return None
            artifact = session.get(ArtifactRecord, mapping.artifact_sha256)
            if artifact is None:
                raise RuntimeError("artifact mapping references a missing artifact")
            from pathlib import Path

            return StoredArtifact(artifact.sha256, artifact.content_type, artifact.byte_size, Path(artifact.storage_path))

    def list_action_reviews(self, run_id: str) -> list[ActionReview]:
        with self._sessions() as session:
            rows = session.scalars(select(ActionReviewRecord).where(ActionReviewRecord.run_id == run_id).order_by(ActionReviewRecord.review_id)).all()
            return [ActionReview(row.action_id, row.version, row.decision, row.reviewer_id, row.reviewer_role, row.rationale, json.loads(row.assumptions_json), _as_utc(row.created_at)) for row in rows]

    def record_action_review(self, *, run_id: str, action_id: str, decision: str, reviewer_id: str, reviewer_role: str, rationale: str, assumptions: dict[str, object]) -> ActionReview:
        with self._sessions.begin() as session:
            run = session.get(RunRecord, run_id)
            if run is None:
                raise UnknownRunError(run_id)
            if run.state != RunState.AWAITING_HUMAN_REVIEW.value:
                raise InvalidTransitionError("reviews require a run awaiting human review")
            version = (session.scalar(select(func.max(ActionReviewRecord.version)).where(ActionReviewRecord.run_id == run_id, ActionReviewRecord.action_id == action_id)) or 0) + 1
            now = _now()
            row = ActionReviewRecord(run_id=run_id, action_id=action_id, version=version, decision=decision, reviewer_id=reviewer_id, reviewer_role=reviewer_role, rationale=rationale, assumptions_json=_canonical_json(assumptions), created_at=now)
            session.add(row)
            self._append_event(session, run, event_type="human_review_recorded", status="completed", message=f"Qualified reviewer recorded {decision} for draft action {action_id}.")
            return ActionReview(action_id, version, decision, reviewer_id, reviewer_role, rationale, assumptions, now)

    def _require_owned_run(self, session: Session, run_id: str, worker_id: str) -> RunRecord:
        record = session.get(RunRecord, run_id)
        if record is None:
            raise UnknownRunError(run_id)
        lease_expires_at = _as_utc(record.lease_expires_at)
        if record.lease_owner != worker_id or lease_expires_at is None or lease_expires_at <= _now():
            raise LeaseOwnershipError(f"worker {worker_id} does not own an active lease for {run_id}")
        return record

    @staticmethod
    def _append_event(
        session: Session,
        record: RunRecord,
        *,
        event_type: str,
        status: str,
        message: str,
        evidence_ids: tuple[str, ...] = (),
        retry_count: int = 0,
    ) -> None:
        maximum = session.scalar(select(func.max(RunEventRecord.sequence)).where(RunEventRecord.run_id == record.run_id))
        session.add(
            RunEventRecord(
                run_id=record.run_id,
                sequence=(maximum or 0) + 1,
                event_type=event_type,
                stage=record.state,
                status=status,
                message=message,
                evidence_ids_json=_canonical_json(list(evidence_ids)),
                retry_count=retry_count,
                created_at=_now(),
            )
        )


def _snapshot(record: RunRecord) -> RunSnapshot:
    return RunSnapshot(
        run_id=record.run_id,
        case_id=record.case_id,
        mode=RunMode(record.mode),
        state=RunState(record.state),
        fixture_mode=record.fixture_mode,
        config=json.loads(record.config_json),
        config_hash=record.config_hash,
        stage_attempt=record.stage_attempt,
        lease_owner=record.lease_owner,
        lease_expires_at=_as_utc(record.lease_expires_at),
        started_at=_as_utc(record.started_at),
        completed_at=_as_utc(record.completed_at),
        created_at=_as_utc(record.created_at),
        updated_at=_as_utc(record.updated_at),
    )


def _event(row: RunEventRecord) -> RunEvent:
    return RunEvent(
        sequence=row.sequence,
        event_type=row.event_type,
        stage=RunState(row.stage),
        status=row.status,
        message=row.message,
        evidence_ids=tuple(json.loads(row.evidence_ids_json)),
        retry_count=row.retry_count,
        created_at=_as_utc(row.created_at),
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _now() -> datetime:
    return datetime.now(UTC)
