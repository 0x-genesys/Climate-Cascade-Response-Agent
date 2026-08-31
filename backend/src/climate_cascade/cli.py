"""Local command line entry point for the direct-prompt baseline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from climate_cascade.baseline import OpenAIChatCompletionsGateway, run_baseline
from climate_cascade.baseline.runner import BaselineRunArtifact, BaselineRunStatus, write_run_artifact
from climate_cascade.agents import ResponseSupervisorRunArtifact
from climate_cascade.domain import VerifiedEvidencePackage, load_frozen_case
from climate_cascade.environment import load_project_environment
from climate_cascade.evaluation import AgentEvaluationStatus, CoverageAdjudication, evaluate_agent_run, evaluate_baseline
from climate_cascade.evaluation.scoring import EvaluationStatus


def main(argv: list[str] | None = None) -> int:
    """Run one baseline call and write an evaluation report beside its artifact."""

    load_project_environment()
    args = _parse_args(argv)
    case = load_frozen_case(args.case)
    gateway = _configured_gateway(args)
    run = run_baseline(case, gateway)
    write_run_artifact(args.output, run)

    report = evaluate_baseline(case, run)
    _write_json(args.evaluation_output, report.model_dump(mode="json"))
    print(
        json.dumps(
            {
                "run_status": run.status,
                "evaluation_status": report.status,
                "run_artifact": str(args.output),
                "evaluation_artifact": str(args.evaluation_output),
            },
            sort_keys=True,
        )
    )
    return 0 if run.status is BaselineRunStatus.COMPLETED else 2


def evaluate_main(argv: list[str] | None = None) -> int:
    """Evaluate an existing baseline run without issuing another model request."""

    load_project_environment()
    args = _parse_evaluate_args(argv)
    case = load_frozen_case(args.case)
    run = BaselineRunArtifact.model_validate_json(args.run.read_text(encoding="utf-8"))
    adjudication = _load_adjudication(args.adjudication)
    report = evaluate_baseline(case, run, adjudication)
    _write_json(args.evaluation_output, report.model_dump(mode="json"))
    print(
        json.dumps(
            {
                "run_id": run.run_id,
                "evaluation_status": report.status,
                "evaluation_artifact": str(args.evaluation_output),
            },
            sort_keys=True,
        )
    )
    return 0 if report.status is EvaluationStatus.COMPLETE else 2


def evaluate_agent_main(argv: list[str] | None = None) -> int:
    """Evaluate a stored response-supervisor draft without making a model request."""

    load_project_environment()
    args = _parse_evaluate_agent_args(argv)
    case = load_frozen_case(args.case)
    run = ResponseSupervisorRunArtifact.model_validate_json(args.run.read_text(encoding="utf-8"))
    evidence = VerifiedEvidencePackage.model_validate_json(args.evidence.read_text(encoding="utf-8"))
    adjudication = _load_adjudication(args.adjudication) if args.adjudication is not None else None
    report = evaluate_agent_run(run=run, evidence=evidence, case=case, adjudication=adjudication)
    _write_json(args.evaluation_output, report.model_dump(mode="json"))
    print(
        json.dumps(
            {
                "run_id": run.run_id,
                "evaluation_status": report.status,
                "evaluation_artifact": str(args.evaluation_output),
            },
            sort_keys=True,
        )
    )
    return 0 if report.status is AgentEvaluationStatus.COMPLETE else 2


def create_live_comparison_adjudication_main(argv: list[str] | None = None) -> int:
    """Create two explicit human-decision templates from a frozen rubric."""
    args = _parse_live_template_args(argv)
    case = load_frozen_case(args.case)
    baseline = json.loads(args.baseline_run.read_text(encoding="utf-8"))["baseline_run"]
    agent = json.loads(args.agent_run.read_text(encoding="utf-8"))["response_supervisor_run"]
    decisions = [{"gold_action_id": item.gold_action_id, "covered": None, "proposal_action_id": None, "rationale": "Fill after human review."} for item in case.gold_actions.actions]
    payload = {"schema_version": "1", "rubric_case_id": case.manifest.fixture_id, "claim_boundary": "Rubric transfer only unless this rubric was frozen before both live runs.", "baseline": {"run_id": baseline["run_id"], "decisions": decisions}, "agent": {"run_id": agent["run_id"], "decisions": decisions}}
    _write_json(args.output, payload)
    print(json.dumps({"adjudication_template": str(args.output)}, sort_keys=True))
    return 0


def evaluate_live_comparison_main(argv: list[str] | None = None) -> int:
    """Score human-entered paired rubric-transfer decisions without calling an LLM."""
    args = _parse_live_evaluate_args(argv)
    case = load_frozen_case(args.case)
    template = json.loads(args.adjudication.read_text(encoding="utf-8"))
    if any(item["covered"] is None for side in ("baseline", "agent") for item in template[side]["decisions"]):
        raise ValueError("complete every covered decision before evaluation")
    from climate_cascade.evaluation.scoring import CoverageAdjudication
    baseline = BaselineRunArtifact.model_validate(json.loads(args.baseline_run.read_text(encoding="utf-8"))["baseline_run"]).model_copy(update={"case_id": case.manifest.fixture_id})
    agent = ResponseSupervisorRunArtifact.model_validate(json.loads(args.agent_run.read_text(encoding="utf-8"))["response_supervisor_run"]).model_copy(update={"case_id": case.manifest.fixture_id})
    evidence = VerifiedEvidencePackage.model_validate(json.loads(args.evidence.read_text(encoding="utf-8"))["source_evidence_package"])
    def adjudication(side, run_id):
        return CoverageAdjudication(case_id=case.manifest.fixture_id, run_id=run_id, reviewer_id=args.reviewer_id, reviewer_role=args.reviewer_role, decided_at=args.decided_at, decisions=template[side]["decisions"])
    output = {"claim_boundary": template["claim_boundary"], "baseline": evaluate_baseline(case, baseline, adjudication("baseline", baseline.run_id)).model_dump(mode="json"), "agent": evaluate_agent_run(run=agent, evidence=evidence, case=case, adjudication=adjudication("agent", agent.run_id)).model_dump(mode="json")}
    _write_json(args.output, output)
    print(json.dumps({"evaluation_output": str(args.output), "claim_boundary": output["claim_boundary"]}, sort_keys=True))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the one-call Climate Cascade baseline.")
    parser.add_argument("--case", type=Path, required=True, help="Frozen case directory.")
    parser.add_argument("--output", type=Path, required=True, help="Path for the run artifact JSON.")
    parser.add_argument(
        "--evaluation-output", type=Path, required=True, help="Path for the evaluation report JSON."
    )
    parser.add_argument("--provider", choices=["openai"], default="openai")
    parser.add_argument("--model", required=True, help="Structured-output model identifier available to the account.")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    return parser.parse_args(argv)


def _parse_evaluate_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate an existing Climate Cascade baseline run.")
    parser.add_argument("--case", type=Path, required=True, help="Frozen case directory.")
    parser.add_argument("--run", type=Path, required=True, help="Completed baseline run artifact JSON.")
    parser.add_argument("--adjudication", type=Path, required=True, help="Completed human coverage-adjudication JSON.")
    parser.add_argument("--evaluation-output", type=Path, required=True, help="Path for the evaluation report JSON.")
    return parser.parse_args(argv)


def _parse_evaluate_agent_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a stored Climate Cascade response-supervisor run.")
    parser.add_argument("--case", type=Path, required=True, help="Frozen case directory.")
    parser.add_argument("--run", type=Path, required=True, help="Response-supervisor run artifact JSON.")
    parser.add_argument("--evidence", type=Path, required=True, help="Stored verified evidence-package JSON.")
    parser.add_argument("--adjudication", type=Path, help="Completed human coverage-adjudication JSON.")
    parser.add_argument("--evaluation-output", type=Path, required=True, help="Path for the evaluation report JSON.")
    return parser.parse_args(argv)


def _parse_live_template_args(argv):
    parser = argparse.ArgumentParser(description="Create paired live-comparison human adjudication template.")
    parser.add_argument("--case", type=Path, required=True); parser.add_argument("--baseline-run", type=Path, required=True); parser.add_argument("--agent-run", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def _parse_live_evaluate_args(argv):
    from datetime import datetime
    parser = argparse.ArgumentParser(description="Evaluate paired live-comparison human decisions.")
    parser.add_argument("--case", type=Path, required=True); parser.add_argument("--baseline-run", type=Path, required=True); parser.add_argument("--agent-run", type=Path, required=True); parser.add_argument("--evidence", type=Path, required=True); parser.add_argument("--adjudication", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--reviewer-id", required=True); parser.add_argument("--reviewer-role", required=True); parser.add_argument("--decided-at", type=datetime.fromisoformat, required=True)
    return parser.parse_args(argv)


def _configured_gateway(args: argparse.Namespace) -> OpenAIChatCompletionsGateway | None:
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        return None
    if args.provider != "openai":
        raise ValueError(f"unsupported provider: {args.provider}")
    return OpenAIChatCompletionsGateway(api_key=api_key, model=args.model)


def _load_adjudication(path: Path) -> CoverageAdjudication:
    return CoverageAdjudication.model_validate_json(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
