from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from climate_cascade.domain import FrozenCaseIntegrityError, load_frozen_case

CASE_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "cases" / "nepal-emsr927-v1"
)


def test_nepal_baseline_case_loads_with_verified_hashes_and_references() -> None:
    case = load_frozen_case(CASE_DIRECTORY)

    assert case.manifest.fixture_id == "nepal-emsr927-v1"
    assert case.manifest.run_mode.value == "baseline"
    assert case.dossier.impact_summary.affected_population == 5300
    assert case.dossier.impact_summary.affected_bridge_features == 26
    assert {action.gold_action_id for action in case.gold_actions.actions} == {
        "verify-access-timure",
        "triage-residential-impact-bidur",
        "check-critical-services-syapru-besi",
        "preserve-bharatpur-data-gap",
    }


def test_frozen_case_rejects_a_modified_artifact(tmp_path: Path) -> None:
    copied_case = tmp_path / "nepal-emsr927-v1"
    shutil.copytree(CASE_DIRECTORY, copied_case)
    dossier_path = copied_case / "incident_dossier.json"
    dossier_path.write_text(dossier_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(FrozenCaseIntegrityError, match="checksum mismatch"):
        load_frozen_case(copied_case)


def test_frozen_case_rejects_unknown_gold_action_reference(tmp_path: Path) -> None:
    copied_case = tmp_path / "nepal-emsr927-v1"
    shutil.copytree(CASE_DIRECTORY, copied_case)
    gold_actions_path = copied_case / "gold_actions.json"
    gold_actions = json.loads(gold_actions_path.read_text(encoding="utf-8"))
    gold_actions["actions"][0]["source_ids"] = ["unknown-source"]
    gold_actions_path.write_text(json.dumps(gold_actions, indent=2) + "\n", encoding="utf-8")

    manifest_path = copied_case / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][2]["sha256"] = sha256(gold_actions_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(FrozenCaseIntegrityError, match="unknown sources"):
        load_frozen_case(copied_case)
