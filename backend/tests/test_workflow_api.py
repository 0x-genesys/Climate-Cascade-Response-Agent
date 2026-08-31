from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from climate_cascade.api import build_services, create_app
from climate_cascade.baseline.gateway import ModelCompletion
from climate_cascade.domain import RunMode, RunState, load_frozen_case
from climate_cascade.persistence import LocalArtifactStore, RunRepository, create_sqlite_engine, migrate_database, sqlite_url
from climate_cascade.sources import build_fixture_evidence_package
from climate_cascade.workflow import WorkflowEngine


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CASE_ROOT = REPOSITORY_ROOT / "data" / "fixtures" / "cases"
DASHBOARD_ROOT = REPOSITORY_ROOT / "dashboard"


class StaticGateway:
    def complete_json(
        self, *, system_prompt: str, user_prompt: str, schema: dict, schema_name: str = "baseline_action_response"
    ) -> ModelCompletion:
        evidence_id = "cems-activation-snapshot" if schema_name == "response_supervisor_action_response" else "cems-activation"
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
                            "evidence_ids": [evidence_id],
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

    listed = client.get("/v1/runs?limit=25")
    assert listed.status_code == 200
    assert listed.json()["runs"][0]["run_id"] == run_id


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


def test_worker_runs_agent_source_intake_to_impact_block(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "workflow.db")
    migrate_database(database_url, repository_root=REPOSITORY_ROOT)
    repository = RunRepository(create_sqlite_engine(database_url))
    run, _ = repository.create_run(
        case_id="nepal-emsr927-v1",
        mode=RunMode.AGENT,
        fixture_mode=True,
        config={"model": "static-test-model"},
        idempotency_key="agent-source-test-key",
    )
    engine = WorkflowEngine(
        repository=repository,
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
        case_root=CASE_ROOT,
        gateway_factory=lambda _config: StaticGateway(),
        response_supervisor_config_path=REPOSITORY_ROOT / "config" / "agents" / "response_supervisor.json",
    )

    result = engine.process_next(worker_id="agent-source-worker")

    assert result is not None
    assert result.state is RunState.AWAITING_HUMAN_REVIEW
    evidence_artifact = repository.get_artifact(run.run_id, "source_evidence_package")
    assert evidence_artifact is not None
    evidence = json.loads(evidence_artifact.storage_path.read_text(encoding="utf-8"))
    assert evidence["verification_status"] == "preliminary"
    assert evidence["activation_code"] == "EMSR927"
    event_types = [event.event_type for event in repository.list_events(run.run_id)]
    assert "source_verified" in event_types
    assert "source_snapshot_pinned" in event_types
    assert "source_intake_started" in event_types
    assert "impact_analysis_started" in event_types
    assert "impact_analysis_completed" in event_types
    assert "response_supervisor_started" in event_types
    assert "response_supervisor_response_received" in event_types
    assert "response_supervisor_completed" in event_types
    assert "evidence_safety_review_completed" in event_types
    assert "draft_checks_started" in event_types
    assert "agent_evaluation_completed" in event_types
    assert repository.get_artifact(run.run_id, "response_supervisor_run") is not None
    assert repository.get_artifact(run.run_id, "agent_evaluation") is not None
    assert repository.get_artifact(run.run_id, "impact_package") is not None
    assert repository.get_artifact(run.run_id, "evidence_safety_review") is not None


def test_api_agent_run_allows_live_activation_and_exposes_evidence(tmp_path: Path) -> None:
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
        "/v1/agent/runs",
        headers={"Idempotency-Key": "api-agent-live-key"},
        json={
            "case_id": "emsr756",
            "mode": "agent",
            "fixture_mode": False,
            "activation": "EMSR756",
            "model": "static-test-model",
        },
    )
    assert created.status_code == 202
    run_id = created.json()["run_id"]
    case = load_frozen_case(CASE_ROOT / "nepal-emsr927-v1")
    engine = WorkflowEngine(
        repository=services.repository,
        artifact_store=LocalArtifactStore(artifact_root),
        case_root=CASE_ROOT,
        gateway_factory=lambda _config: StaticGateway(),
        evidence_package_factory=lambda _run: build_fixture_evidence_package(case),
        response_supervisor_config_path=REPOSITORY_ROOT / "config" / "agents" / "response_supervisor.json",
    )

    engine.process_next(worker_id="api-agent-source-worker")

    status = client.get(f"/v1/runs/{run_id}")
    evidence = client.get(f"/v1/runs/{run_id}/evidence")
    assert status.json()["state"] == "blocked"
    assert evidence.status_code == 200
    assert evidence.json()["source_evidence_package"]["activation_code"] == "EMSR927"
    agent = client.get(f"/v1/runs/{run_id}/agent")
    assert agent.json()["response_supervisor_run"]["status"] == "failed"


def test_api_exposes_saved_impact_package(tmp_path: Path) -> None:
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
        "/v1/agent/runs",
        headers={"Idempotency-Key": "api-agent-impact-key"},
        json={"case_id": "nepal-emsr927-v1", "mode": "agent", "fixture_mode": True, "model": "static-test-model"},
    )
    engine = WorkflowEngine(
        repository=services.repository,
        artifact_store=LocalArtifactStore(artifact_root),
        case_root=CASE_ROOT,
        gateway_factory=lambda _config: StaticGateway(),
        response_supervisor_config_path=REPOSITORY_ROOT / "config" / "agents" / "response_supervisor.json",
    )

    engine.process_next(worker_id="api-agent-impact-worker")

    payload = client.get(f"/v1/runs/{created.json()['run_id']}/impacts")
    assert payload.status_code == 200
    assert payload.json()["impact_package"]["status"] == "incomplete"
    assert "No raw CEMS activation snapshot" in payload.json()["impact_package"]["data_gaps"][0]
    agent = client.get(f"/v1/runs/{created.json()['run_id']}/agent")
    assert agent.json()["evidence_safety_review"]["verdict"] == "pass"


def test_api_serves_dashboard_static_files(tmp_path: Path) -> None:
    services = build_services(
        database_url=sqlite_url(tmp_path / "workflow.db"),
        artifact_root=tmp_path / "artifacts",
        case_root=CASE_ROOT,
        repository_root=REPOSITORY_ROOT,
        dashboard_root=DASHBOARD_ROOT,
    )
    client = TestClient(create_app(services=services))

    index = client.get("/")
    script = client.get("/dashboard/app.js")

    assert index.status_code == 200
    assert "Climate Cascade Response" in index.text
    assert script.status_code == 200
    assert "/v1/runs?limit=25" in script.text
    assert "/v1/runs/${state.runId}/evidence" in script.text
    assert "/v1/runs/${state.runId}/impacts" in script.text
    assert "Life-safety estimate:" in script.text
    assert "Drafts rejected" in script.text
    assert "Draft checks did not run:" in script.text
    assert "liveStatus" in index.text
    assert "response_supervisor_started" in script.text
    assert "Glossary: terms used in this review" in index.text
    assert "Life-Safety Action Coverage at 5" in index.text
    assert "What finished CEMS products show" in index.text
