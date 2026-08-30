from __future__ import annotations

import json
from pathlib import Path

from climate_cascade.cli import main

CASE_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "cases" / "nepal-emsr927-v1"
)


def test_cli_writes_a_fail_closed_artifact_when_no_api_key_is_available(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
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
