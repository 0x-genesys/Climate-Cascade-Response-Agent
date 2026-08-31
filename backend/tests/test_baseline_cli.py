from __future__ import annotations

import json
from pathlib import Path

from climate_cascade.baseline.runner import run_baseline, write_run_artifact
import climate_cascade.cli as cli_module
from climate_cascade.cli import evaluate_main, main
from climate_cascade.evaluation import CoverageAdjudication
from climate_cascade.domain import load_frozen_case

from test_baseline_runner import StaticGateway, valid_response

CASE_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "cases" / "nepal-emsr927-v1"
)


def test_cli_writes_a_fail_closed_artifact_when_no_api_key_is_available(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli_module, "load_project_environment", lambda: Path(".env"))
    run_path = tmp_path / "run.json"
    evaluation_path = tmp_path / "evaluation.json"

    status = main(
        [
            "--case",
            str(CASE_DIRECTORY),
            "--output",
            str(run_path),
            "--evaluation-output",
            str(evaluation_path),
            "--model",
            "test-model",
        ]
    )

    assert status == 2
    assert json.loads(run_path.read_text(encoding="utf-8"))["failure_code"] == "provider_not_configured"
    assert json.loads(evaluation_path.read_text(encoding="utf-8"))["status"] == "run_failed"


def test_evaluation_cli_scores_a_saved_run_without_a_model_request(tmp_path: Path) -> None:
    case = load_frozen_case(CASE_DIRECTORY)
    run = run_baseline(case, StaticGateway(valid_response()))
    run_path = tmp_path / "run.json"
    adjudication_path = tmp_path / "adjudication.json"
    evaluation_path = tmp_path / "evaluation.json"
    write_run_artifact(run_path, run)
    adjudication = CoverageAdjudication(
        case_id=case.manifest.fixture_id,
        run_id=run.run_id,
        reviewer_id="manual-reviewer",
        reviewer_role="emergency operations analyst",
        decided_at="2026-08-30T10:00:00Z",
        decisions=[
            {
                "gold_action_id": "verify-access-timure",
                "covered": True,
                "proposal_action_id": "timure-access-review",
                "rationale": "The proposal keeps Timure access verification under human review.",
            },
            {
                "gold_action_id": "triage-residential-impact-bidur",
                "covered": True,
                "proposal_action_id": "bidur-impact-review",
                "rationale": "The proposal targets cited residential impact evidence in Bidur.",
            },
            {
                "gold_action_id": "check-critical-services-syapru-besi",
                "covered": False,
                "rationale": "The saved baseline response does not address Syapru Besi services.",
            },
            {
                "gold_action_id": "preserve-bharatpur-data-gap",
                "covered": False,
                "rationale": "The saved baseline response does not request evidence for Bharatpur.",
            },
        ],
    )
    adjudication_path.write_text(adjudication.model_dump_json(indent=2) + "\n", encoding="utf-8")

    status = evaluate_main(
        [
            "--case",
            str(CASE_DIRECTORY),
            "--run",
            str(run_path),
            "--adjudication",
            str(adjudication_path),
            "--evaluation-output",
            str(evaluation_path),
        ]
    )

    report = json.loads(evaluation_path.read_text(encoding="utf-8"))
    assert status == 0
    assert report["status"] == "complete"
    assert report["lsac_at_5"]["value"] == 10 / 17
