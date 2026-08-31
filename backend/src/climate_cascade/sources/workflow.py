"""Workflow-facing source evidence package selection."""

from __future__ import annotations

from pathlib import Path

from climate_cascade.domain import VerifiedEvidencePackage, load_frozen_case
from climate_cascade.persistence import RunSnapshot

from .cems import CemsActivationAdapter
from .fixture import build_fixture_evidence_package


def build_evidence_package_for_run(*, run: RunSnapshot, case_root: Path) -> VerifiedEvidencePackage:
    if run.fixture_mode:
        return build_fixture_evidence_package(load_frozen_case(case_root / run.case_id))
    activation = run.config.get("activation")
    if not isinstance(activation, str) or not activation.strip():
        raise ValueError("live source-intake runs require an activation code")
    return CemsActivationAdapter().fetch(activation, case_id=run.case_id)
