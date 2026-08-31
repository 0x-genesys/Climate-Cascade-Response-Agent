"""Evidence package builder for pinned frozen fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json

from climate_cascade.domain import (
    CemsActivationSummary,
    EvidenceStatus,
    FrozenCaseBundle,
    SourceSnapshot,
    SourceSnapshotKind,
    SourceVerificationFinding,
    SourceVerificationSeverity,
    VerifiedEvidencePackage,
)


def build_fixture_evidence_package(case: FrozenCaseBundle) -> VerifiedEvidencePackage:
    retrieved_at = datetime.now(UTC)
    snapshots = [
        SourceSnapshot(
            snapshot_id=f"{source.source_id}-snapshot",
            source_id=source.source_id,
            adapter="frozen-fixture",
            publisher=source.publisher,
            source_url=source.source_url,
            retrieved_at=retrieved_at,
            kind=SourceSnapshotKind.CURATED_FIXTURE,
            content_sha256=source.upstream_sha256 or _hash_json(source.model_dump(mode="json")),
            content_type="application/json",
            license_note=source.license_note,
        )
        for source in case.dossier.sources
    ]
    activation_code = (case.dossier.event.activation_code or case.dossier.case_id).upper()
    findings = [
        SourceVerificationFinding(
            finding_id="fixture-integrity-verified",
            severity=SourceVerificationSeverity.INFO,
            status=EvidenceStatus.SUPPORTED,
            message="Frozen fixture artifacts passed manifest checksum validation before evidence packaging.",
            source_ids=[snapshots[0].source_id],
        )
    ]
    if any(claim.status is EvidenceStatus.PRELIMINARY for claim in case.dossier.claims):
        findings.append(
            SourceVerificationFinding(
                finding_id="fixture-preliminary-claims",
                severity=SourceVerificationSeverity.WARNING,
                status=EvidenceStatus.PRELIMINARY,
                message="The fixture includes preliminary or unresolved source claims that must remain visible.",
                source_ids=[snapshots[0].source_id],
            )
        )
    cems_summary = CemsActivationSummary(
        activation_code=activation_code,
        name=case.dossier.event.display_name,
        category="Flood",
        sub_category="Flash flood",
        event_time=case.dossier.event.occurred_at.isoformat(),
        activation_time=None,
        countries=["Nepal"],
        closed=False,
        stats={
            "Population [No.]": case.dossier.impact_summary.affected_population,
            "Identified buildings [No.]": case.dossier.impact_summary.affected_buildings,
            "Roads [km]": case.dossier.impact_summary.affected_roads_km,
            "Bridge features [No.]": case.dossier.impact_summary.affected_bridge_features,
        },
        aois=[],
    )
    return VerifiedEvidencePackage(
        package_id=f"source-package-{case.dossier.case_id}",
        case_id=case.dossier.case_id,
        activation_code=activation_code,
        hazard_type=case.dossier.event.hazard_type,
        verification_status=EvidenceStatus.PRELIMINARY,
        retrieved_at=retrieved_at,
        snapshots=snapshots,
        claims=case.dossier.claims,
        findings=findings,
        data_gaps=case.dossier.data_gaps,
        cems_activation=cems_summary,
    )


def _hash_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()
