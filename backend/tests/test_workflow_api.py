from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from climate_cascade.api import build_services, create_app
from climate_cascade.baseline.gateway import ModelCompletion
from climate_cascade.domain import RunMode, RunState
from climate_cascade.persistence import LocalArtifactStore, RunRepository, create_sqlite_engine, migrate_database, sqlite_url
from climate_cascade.workflow import WorkflowEngine


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CASE_ROOT = REPOSITORY_ROOT / "data" / "fixtures" / "cases"


class StaticGateway:
    def complete_json(self, *, system_prompt: str, user_prompt: str, schema: dict) -> ModelCompletion:
        return ModelCompletion(
            raw_response=json.dumps(
                {
                    "schema_version": "1",
                    "case_id": "nepal-emsr927-v1",
                    "actions": [
                        {
                            "schema_version": "1",
                            "action_id": "request-bharatpur-evidence",
                            "title": "Request pending Bharatpur evidence",
                            "location_ref": "Bharatpur AOI",
                            "owner_role": "emergency operations analyst",
                            "urgency": "under_six_hours",
                            "evidence_ids": ["cems-activation"],
                            "status": "draft",
                            "estimate": None,
                        }
                    ],
                    "limitations": ["No deterministic impact analysis is available in the baseline."],
                }
            ),
            provider="test",
            model="static-test-model",
            prompt_tokens=10,
            completion_tokens=20,
        )


def test_repository_applies_migrations_and_enforces_idempotency(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "workflow.db")
    migrate_database(database_url, repository_root=REPOSITORY_ROOT)
    repository = RunRepository(create_sqlite_engine(database_url))

    first, created = repository.create_run(
        case_id="nepal-emsr927-v1",
        mode=RunMode.BASELINE,
        fixture_mode=True,
        config={"model": "static-test-model"},
        idempotency_key="baseline-test-key",
    )
    second, duplicate = repository.create_run(
        case_id="nepal-emsr927-v1",
        mode=RunMode.BASELINE,
        fixture_mode=True,
        config={"model": "static-test-model"},
        idempotency_key="baseline-test-key",
    )

    assert created is True
    assert duplicate is False
    assert first.run_id == second.run_id
    assert [event.sequence for event in repository.list_events(first.run_id)] == [1]


def test_worker_leases_and_runs_baseline_to_human_review(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "workflow.db")
    migrate_database(database_url, repository_root=REPOSITORY_ROOT)
    repository = RunRepository(create_sqlite_engine(database_url))
    run, _ = repository.create_run(
        case_id="nepal-emsr927-v1",
        mode=RunMode.BASELINE,
        fixture_mode=True,
        config={"model": "static-test-model"},
        idempotency_key="worker-test-key",
    )
    engine = WorkflowEngine(
        repository=repository,
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
        case_root=CASE_ROOT,
        gateway_factory=lambda _config: StaticGateway(),
        lease_seconds=30,
    )

    result = engine.process_next(worker_id="test-worker")

    assert result is not None
    assert result.state is RunState.AWAITING_HUMAN_REVIEW
    final = repository.get_run(run.run_id)
    assert final.lease_owner is None
    assert repository.get_artifact(run.run_id, "baseline_run") is not None
    assert repository.get_artifact(run.run_id, "baseline_evaluation") is not None
    events = repository.list_events(run.run_id)
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert events[-2].event_type == "baseline_evaluated"


def test_expired_lease_can_be_reclaimed(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "workflow.db")
    migrate_database(database_url, repository_root=REPOSITORY_ROOT)
    repository = RunRepository(create_sqlite_engine(database_url))
    run, _ = repository.create_run(
        case_id="nepal-emsr927-v1",
        mode=RunMode.BASELINE,
        fixture_mode=True,
        config={"model": "static-test-model"},
        idempotency_key="lease-reclaim-key",
    )

    first = repository.lease_next_run(worker_id="first-worker", lease_seconds=0)
    second = repository.lease_next_run(worker_id="second-worker", lease_seconds=30)

    assert first is not None
    assert first.run_id == run.run_id
    assert second is not None
    assert second.run_id == run.run_id
    assert second.lease_owner == "second-worker"


def test_api_creates_idempotent_run_and_replays_sse_events(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "workflow.db")
    services = build_services(
        database_url=database_url,
        artifact_root=tmp_path / "artifacts",
        case_root=CASE_ROOT,
        repository_root=REPOSITORY_ROOT,
    )
    client = TestClient(create_app(services=services))
    headers = {"Idempotency-Key": "api-baseline-key"}
    payload = {"case_id": "nepal-emsr927-v1", "mode": "baseline", "fixture_mode": True, "model": "static-test-model"}

    first = client.post("/v1/runs", headers=headers, json=payload)
    second = client.post("/v1/runs", headers=headers, json=payload)

    assert first.status_code == 202
    assert second.status_code == 202
    run_id = first.json()["run_id"]
    assert second.json()["run_id"] == run_id
    events = client.get(f"/v1/runs/{run_id}/events?follow=false")
    assert events.status_code == 200
    assert "event: run_event" in events.text
    assert '"event_type":"run_created"' in events.text


def test_api_baseline_run_exposes_worker_artifacts(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "workflow.db")
    artifact_root = tmp_path / "artifacts"
    services = build_services(
        database_url=database_url,
        artifact_root=artifact_root,
        case_root=CASE_ROOT,
        repository_root=REPOSITORY_ROOT,
    )
    client = TestClient(create_app(services=services))
    created = client.post(
        "/v1/baseline/runs",
        headers={"Idempotency-Key": "api-worker-baseline-key"},
        json={"case_id": "nepal-emsr927-v1", "model": "static-test-model"},
    )
    assert created.status_code == 202
    run_id = created.json()["run_id"]
    engine = WorkflowEngine(
        repository=services.repository,
        artifact_store=LocalArtifactStore(artifact_root),
        case_root=CASE_ROOT,
        gateway_factory=lambda _config: StaticGateway(),
    )

    engine.process_next(worker_id="api-worker")

    status = client.get(f"/v1/runs/{run_id}")
    artifacts = client.get(f"/v1/runs/{run_id}/baseline")
    assert status.json()["state"] == "awaiting_human_review"
    assert artifacts.json()["baseline_run"]["status"] == "completed"
    assert artifacts.json()["baseline_evaluation"]["status"] == "not_evaluable"
