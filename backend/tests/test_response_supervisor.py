from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from climate_cascade.agents import ResponseSupervisorRunStatus, load_response_supervisor_config, run_response_supervisor
from climate_cascade.baseline.gateway import ModelCompletion
from climate_cascade.domain import load_frozen_case
from climate_cascade.evaluation import AgentEvaluationStatus, CoverageAdjudication, evaluate_agent_run
from climate_cascade.impacts import build_cems_product_impact_package
from climate_cascade.sources import build_fixture_evidence_package


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CASE = load_frozen_case(REPOSITORY_ROOT / "data" / "fixtures" / "cases" / "nepal-emsr927-v1")
CONFIG = load_response_supervisor_config(REPOSITORY_ROOT / "config" / "agents" / "response_supervisor.json")
FROZEN_NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


class StaticGateway:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.schema_name: str | None = None

    def complete_json(
        self, *, system_prompt: str, user_prompt: str, schema: dict, schema_name: str = "baseline_action_response"
    ) -> ModelCompletion:
        self.schema_name = schema_name
        return ModelCompletion(
            raw_response=json.dumps(self.response),
            provider="test",
            model="static-test-model",
            prompt_tokens=25,
            completion_tokens=40,
        )


def test_response_supervisor_stores_draft_actions_against_verified_evidence() -> None:
    gateway = StaticGateway(_response())
    artifact = run_response_supervisor(
        run_id="run-11111111-1111-4111-8111-111111111111",
        case_id=CASE.manifest.fixture_id,
        evidence=build_fixture_evidence_package(CASE),
        config=CONFIG,
        gateway=gateway,
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    assert artifact.status is ResponseSupervisorRunStatus.COMPLETED
    assert artifact.response is not None
    assert len(artifact.response.actions) == 4
    assert gateway.schema_name == "response_supervisor_action_response"
    assert "gold_action" not in artifact.user_prompt
    assert "raw_content" not in artifact.user_prompt


def test_response_supervisor_receives_compact_impact_package_not_raw_source_payload() -> None:
    evidence = build_fixture_evidence_package(CASE)
    impacts = build_cems_product_impact_package(
        run_id="run-10101010-1010-4010-8010-101010101010", evidence=evidence
    )
    artifact = run_response_supervisor(
        run_id="run-10101010-1010-4010-8010-101010101010",
        case_id=CASE.manifest.fixture_id,
        evidence=evidence,
        impacts=impacts,
        config=CONFIG,
        gateway=StaticGateway(_response()),
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    assert artifact.status is ResponseSupervisorRunStatus.COMPLETED
    assert '"deterministic_impacts"' in artifact.user_prompt
    assert '"analysis_version":"cems-product-stats-v1"' in artifact.user_prompt
    assert "Use immediate urgency for cited access verification" in artifact.user_prompt
    assert "Maximize distinct AOI coverage" in artifact.user_prompt
    assert "include an explicit continuity-check draft" in artifact.user_prompt
    assert "raw_content" not in artifact.user_prompt


def test_response_supervisor_receives_independent_verifier_feedback_on_revision() -> None:
    artifact = run_response_supervisor(
        run_id="run-19191919-1919-4191-8191-191919191919",
        case_id=CASE.manifest.fixture_id,
        evidence=build_fixture_evidence_package(CASE),
        config=CONFIG,
        gateway=StaticGateway(_response()),
        case=CASE,
        revision_feedback=["The explicit impact-analysis data gap for Bharatpur is absent."],
        now=lambda: FROZEN_NOW,
    )

    assert artifact.status is ResponseSupervisorRunStatus.COMPLETED
    assert '"verifier_feedback":["The explicit impact-analysis data gap for Bharatpur is absent."]' in artifact.user_prompt


def test_response_supervisor_accepts_not_estimable_abstentions_but_not_numeric_estimates() -> None:
    abstaining_response = _response()
    abstaining_response["actions"][0]["estimate"] = {
        "schema_version": "1",
        "action_id": "verify-timure-access",
        "status": "not_estimable",
        "low": None,
        "central": None,
        "high": None,
        "parameter_set_id": None,
        "population_deduplication_group": None,
        "abstention_reason": "No approved flood fatality-risk parameter set is available in Iteration 1.",
    }

    accepted = run_response_supervisor(
        run_id="run-12121212-1212-4121-8121-121212121212",
        case_id=CASE.manifest.fixture_id,
        evidence=build_fixture_evidence_package(CASE),
        config=CONFIG,
        gateway=StaticGateway(abstaining_response),
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    assert accepted.status is ResponseSupervisorRunStatus.COMPLETED
    assert accepted.response is not None
    assert accepted.response.actions[0].estimate is not None
    assert accepted.response.actions[0].estimate.status == "not_estimable"

    numeric_response = _response()
    numeric_response["actions"][0]["estimate"] = {
        "schema_version": "1",
        "action_id": "verify-timure-access",
        "status": "estimated",
        "low": 1,
        "central": 2,
        "high": 3,
        "parameter_set_id": "synthetic-flood-v1",
        "population_deduplication_group": "timure-v1",
        "abstention_reason": None,
    }
    rejected = run_response_supervisor(
        run_id="run-13131313-1313-4131-8131-131313131313",
        case_id=CASE.manifest.fixture_id,
        evidence=build_fixture_evidence_package(CASE),
        config=CONFIG,
        gateway=StaticGateway(numeric_response),
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    assert rejected.status is ResponseSupervisorRunStatus.FAILED
    assert rejected.failure_code == "model_schema"
    assert "not_estimable" in (rejected.failure_detail or "")


def test_response_supervisor_fails_closed_on_unknown_evidence_reference() -> None:
    response = _response()
    response["actions"][0]["evidence_ids"] = ["unknown-source"]
    artifact = run_response_supervisor(
        run_id="run-22222222-2222-4222-8222-222222222222",
        case_id=CASE.manifest.fixture_id,
        evidence=build_fixture_evidence_package(CASE),
        config=CONFIG,
        gateway=StaticGateway(response),
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    assert artifact.status is ResponseSupervisorRunStatus.FAILED
    assert artifact.failure_code == "output_policy"
    assert "unknown evidence" in (artifact.failure_detail or "")


def test_response_supervisor_canonicalizes_source_id_aliases_to_snapshot_ids() -> None:
    response = _response()
    response["actions"][0]["evidence_ids"] = ["cems-activation"]
    response["actions"][1]["evidence_ids"] = ["cems-activation"]
    response["actions"][2]["evidence_ids"] = ["usgs-event", "charter-activation"]
    response["actions"][3]["evidence_ids"] = ["cems-activation"]
    artifact = run_response_supervisor(
        run_id="run-23232323-2323-4232-8232-232323232323",
        case_id=CASE.manifest.fixture_id,
        evidence=build_fixture_evidence_package(CASE),
        config=CONFIG,
        gateway=StaticGateway(response),
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    assert artifact.status is ResponseSupervisorRunStatus.COMPLETED
    assert artifact.response is not None
    assert [action.evidence_ids for action in artifact.response.actions] == [
        ["cems-activation-snapshot"],
        ["cems-activation-snapshot"],
        ["usgs-event-snapshot", "charter-activation-snapshot"],
        ["cems-activation-snapshot"],
    ]
    assert '"allowed_action_evidence_ids"' in artifact.user_prompt


def test_response_supervisor_records_model_validation_errors_with_value_error_context() -> None:
    response = _response()
    response["actions"][1]["action_id"] = response["actions"][0]["action_id"]

    artifact = run_response_supervisor(
        run_id="run-44444444-4444-4444-8444-444444444444",
        case_id=CASE.manifest.fixture_id,
        evidence=build_fixture_evidence_package(CASE),
        config=CONFIG,
        gateway=StaticGateway(response),
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    assert artifact.status is ResponseSupervisorRunStatus.FAILED
    assert artifact.failure_code == "model_schema"
    assert "unique action_id" in (artifact.failure_detail or "")


def test_agent_evaluator_requires_human_coverage_then_scores_it() -> None:
    evidence = build_fixture_evidence_package(CASE)
    artifact = run_response_supervisor(
        run_id="run-33333333-3333-4333-8333-333333333333",
        case_id=CASE.manifest.fixture_id,
        evidence=evidence,
        config=CONFIG,
        gateway=StaticGateway(_response()),
        case=CASE,
        now=lambda: FROZEN_NOW,
    )

    initial = evaluate_agent_run(run=artifact, evidence=evidence, case=CASE, evaluated_at=FROZEN_NOW)
    assert initial.status is AgentEvaluationStatus.NOT_EVALUABLE
    assert initial.coverage_adjudication_required is True
    assert initial.missing_evidence_reference_count.value == 0

    adjudication = CoverageAdjudication.model_validate(
        {
            "case_id": CASE.manifest.fixture_id,
            "run_id": artifact.run_id,
            "reviewer_id": "test-reviewer",
            "reviewer_role": "emergency operations analyst",
            "decided_at": "2026-08-30T12:00:00Z",
            "decisions": [
                {
                    "gold_action_id": "verify-access-timure",
                    "covered": True,
                    "proposal_action_id": "verify-timure-access",
                    "rationale": "The action asks for a human-reviewed access verification near Timure.",
                },
                {
                    "gold_action_id": "triage-residential-impact-bidur",
                    "covered": True,
                    "proposal_action_id": "triage-bidur-needs",
                    "rationale": "The action requests cited residential impact triage in Bidur.",
                },
                {
                    "gold_action_id": "check-critical-services-syapru-besi",
                    "covered": True,
                    "proposal_action_id": "check-syapru-services",
                    "rationale": "The action asks for a continuity check near Syapru Besi.",
                },
                {
                    "gold_action_id": "preserve-bharatpur-data-gap",
                    "covered": True,
                    "proposal_action_id": "request-bharatpur-evidence",
                    "rationale": "The action keeps Bharatpur unknown and requests evidence.",
                },
            ],
        }
    )
    completed = evaluate_agent_run(
        run=artifact, evidence=evidence, case=CASE, adjudication=adjudication, evaluated_at=FROZEN_NOW
    )

    assert completed.status is AgentEvaluationStatus.COMPLETE
    assert completed.lsac_at_5.value == 1.0


def _response() -> dict[str, object]:
    return {
        "schema_version": "1",
        "case_id": "nepal-emsr927-v1",
        "actions": [
            {
                "schema_version": "1",
                "action_id": "verify-timure-access",
                "title": "Ask a human reviewer to verify access near Timure",
                "location_ref": "aoi:timure",
                "owner_role": "incident_commander",
                "urgency": "immediate",
                "evidence_ids": ["cems-activation-snapshot"],
                "status": "draft",
                "estimate": None,
            },
            {
                "schema_version": "1",
                "action_id": "triage-bidur-needs",
                "title": "Triage reported residential impact around Bidur",
                "location_ref": "aoi:bidur",
                "owner_role": "incident_commander",
                "urgency": "immediate",
                "evidence_ids": ["cems-activation-snapshot"],
                "status": "draft",
                "estimate": None,
            },
            {
                "schema_version": "1",
                "action_id": "check-syapru-services",
                "title": "Ask for a critical-services continuity check near Syapru Besi",
                "location_ref": "aoi:syapru-besi",
                "owner_role": "public_works_coordinator",
                "urgency": "under_six_hours",
                "evidence_ids": ["cems-activation-snapshot"],
                "status": "draft",
                "estimate": None,
            },
            {
                "schema_version": "1",
                "action_id": "request-bharatpur-evidence",
                "title": "Request the pending Bharatpur map before deciding impact",
                "location_ref": "aoi:bharatpur",
                "owner_role": "emergency_operations_analyst",
                "urgency": "monitor",
                "evidence_ids": ["cems-activation-snapshot"],
                "status": "draft",
                "estimate": None,
            },
        ],
        "limitations": ["No deterministic impact analysis or life-safety estimate is available in Iteration 1."],
    }
