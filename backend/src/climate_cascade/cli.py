"""Local command line entry point for the direct-prompt baseline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from climate_cascade.baseline import OpenAIChatCompletionsGateway, run_baseline
from climate_cascade.baseline.runner import BaselineRunStatus, write_run_artifact
from climate_cascade.domain import load_frozen_case
from climate_cascade.evaluation import CoverageAdjudication, evaluate_baseline


def main(argv: list[str] | None = None) -> int:
    """Run one baseline call and write an evaluation report beside its artifact."""

    args = _parse_args(argv)
    case = load_frozen_case(args.case)
    gateway = _configured_gateway(args)
    run = run_baseline(case, gateway)
    write_run_artifact(args.output, run)

    adjudication = _load_adjudication(args.adjudication) if args.adjudication else None
    report = evaluate_baseline(case, run, adjudication)
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


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the one-call Climate Cascade baseline.")
    parser.add_argument("--case", type=Path, required=True, help="Frozen case directory.")
    parser.add_argument("--output", type=Path, required=True, help="Path for the run artifact JSON.")
    parser.add_argument(
        "--evaluation-output", type=Path, required=True, help="Path for the evaluation report JSON."
    )
    parser.add_argument("--adjudication", type=Path, help="Optional human coverage-adjudication JSON.")
    parser.add_argument("--provider", choices=["openai"], default="openai")
    parser.add_argument("--model", required=True, help="Structured-output model identifier available to the account.")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
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
