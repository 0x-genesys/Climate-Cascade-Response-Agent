"""Frozen case loading with checksum and cross-reference validation."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from pydantic import ValidationError

from .models import FrozenCaseBundle, FrozenCaseManifest, GoldActionSet, IncidentDossier, OperationalScenario


class FrozenCaseIntegrityError(ValueError):
    """Raised when a case is incomplete, modified, or internally inconsistent."""


def load_frozen_case(case_directory: Path) -> FrozenCaseBundle:
    """Load a case only when every declared artifact hash and reference is valid."""

    root = case_directory.resolve()
    manifest = _load_model(root / "manifest.json", FrozenCaseManifest)
    declared = {artifact.relative_path: artifact.sha256 for artifact in manifest.artifacts}

    for relative_path, expected_hash in declared.items():
        artifact_path = _resolve_artifact(root, relative_path)
        if not artifact_path.is_file():
            raise FrozenCaseIntegrityError(f"declared artifact is missing: {relative_path}")
        actual_hash = _sha256_file(artifact_path)
        if actual_hash != expected_hash:
            raise FrozenCaseIntegrityError(
                f"artifact checksum mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}"
            )

    dossier = _load_model(_resolve_artifact(root, manifest.dossier_path), IncidentDossier)
    scenario = _load_model(_resolve_artifact(root, manifest.scenario_path), OperationalScenario)
    gold_actions = _load_model(_resolve_artifact(root, manifest.gold_actions_path), GoldActionSet)

    if dossier.case_id != manifest.fixture_id:
        raise FrozenCaseIntegrityError("dossier.case_id must match manifest.fixture_id")
    if scenario.case_id != manifest.fixture_id:
        raise FrozenCaseIntegrityError("scenario.case_id must match manifest.fixture_id")
    if gold_actions.case_id != manifest.fixture_id:
        raise FrozenCaseIntegrityError("gold_actions.case_id must match manifest.fixture_id")
    if dossier.event.hazard_type != manifest.hazard_type:
        raise FrozenCaseIntegrityError("dossier event hazard_type must match manifest")

    source_ids = {source.source_id for source in dossier.sources}
    constraint_ids = {constraint.constraint_id for constraint in scenario.constraints}
    for action in gold_actions.actions:
        unknown_sources = set(action.source_ids) - source_ids
        unknown_constraints = set(action.constraint_ids) - constraint_ids
        if unknown_sources:
            raise FrozenCaseIntegrityError(
                f"gold action {action.gold_action_id} references unknown sources: {sorted(unknown_sources)}"
            )
        if unknown_constraints:
            raise FrozenCaseIntegrityError(
                f"gold action {action.gold_action_id} references unknown constraints: {sorted(unknown_constraints)}"
            )

    return FrozenCaseBundle(
        manifest=manifest,
        dossier=dossier,
        scenario=scenario,
        gold_actions=gold_actions,
    )


def _load_model(path: Path, model_type):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return model_type.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise FrozenCaseIntegrityError(f"invalid fixture file {path.name}: {error}") from error


def _resolve_artifact(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents:
        raise FrozenCaseIntegrityError(f"artifact path escapes case directory: {relative_path}")
    return candidate


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as artifact:
        for block in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
