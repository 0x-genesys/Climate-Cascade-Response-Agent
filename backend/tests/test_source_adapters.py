from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from climate_cascade.domain import EvidenceStatus, HazardType, SourceVerificationSeverity, VerifiedEvidencePackage, load_frozen_case
from climate_cascade.sources import CemsActivationAdapter, SourceAdapterError, build_fixture_evidence_package


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CASE_ROOT = REPOSITORY_ROOT / "data" / "fixtures" / "cases"
FROZEN_NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def test_verified_evidence_package_rejects_unknown_source_reference() -> None:
    with pytest.raises(ValidationError, match="unknown sources"):
        VerifiedEvidencePackage.model_validate(
            {
                "package_id": "source-package-test",
                "case_id": "case-test",
                "activation_code": "EMSR927",
                "hazard_type": "flood_debris_flow",
                "verification_status": "supported",
                "retrieved_at": "2026-08-30T12:00:00Z",
                "snapshots": [
                    {
                        "snapshot_id": "cems-emsr927-snapshot",
                        "source_id": "cems-emsr927",
                        "adapter": "cems-rapid-mapping",
                        "publisher": "Copernicus Emergency Management Service",
                        "source_url": "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?code=EMSR927",
                        "retrieved_at": "2026-08-30T12:00:00Z",
                        "kind": "raw_http_json",
                        "content_sha256": "a" * 64,
                        "content_type": "application/json",
                        "license_note": "Public source with citation required.",
                    }
                ],
                "claims": [
                    {
                        "claim_id": "bad-claim",
                        "statement": "This claim references a missing source.",
                        "status": "supported",
                        "source_ids": ["missing-source"],
                    }
                ],
                "findings": [
                    {
                        "finding_id": "source-reachable",
                        "severity": "info",
                        "status": "supported",
                        "message": "Source was reachable.",
                        "source_ids": ["cems-emsr927"],
                    }
                ],
            }
        )


def test_fixture_evidence_package_preserves_preliminary_nepal_gaps() -> None:
    package = build_fixture_evidence_package(load_frozen_case(CASE_ROOT / "nepal-emsr927-v1"))

    assert package.case_id == "nepal-emsr927-v1"
    assert package.activation_code == "EMSR927"
    assert package.hazard_type is HazardType.FLOOD_DEBRIS_FLOW
    assert package.verification_status is EvidenceStatus.PRELIMINARY
    assert {snapshot.source_id for snapshot in package.snapshots} == {
        "cems-activation",
        "usgs-event",
        "charter-activation",
    }
    assert any("Bharatpur" in gap for gap in package.data_gaps)
    assert any(finding.finding_id == "fixture-preliminary-claims" for finding in package.findings)


def test_cems_adapter_parses_activation_and_pending_aoi_status() -> None:
    adapter = CemsActivationAdapter(http_get_json=lambda _url: _cems_payload(category="Flood"), clock=lambda: FROZEN_NOW)

    package = adapter.fetch("EMSR927", case_id="nepal-live")

    assert package.case_id == "nepal-live"
    assert package.activation_code == "EMSR927"
    assert package.verification_status is EvidenceStatus.PRELIMINARY
    assert package.cems_activation is not None
    assert package.cems_activation.finished_product_count == 2
    assert package.cems_activation.pending_product_count == 1
    assert package.cems_activation.stats["Population [No.]"] == 5300
    assert package.snapshots[0].content_sha256 == "2f3782d3517f7d2da54c7feaa30abd3d6fc8840f1e4b4fa03ca87869c95d8823"
    assert package.snapshots[0].raw_content == _cems_payload(category="Flood")
    assert any(finding.finding_id == "cems-activation-open" for finding in package.findings)
    assert any(finding.finding_id == "cems-products-pending" for finding in package.findings)
    assert any("Bharatpur" in gap for gap in package.data_gaps)


def test_cems_adapter_blocks_categories_outside_flood_mvp() -> None:
    adapter = CemsActivationAdapter(http_get_json=lambda _url: _cems_payload(category="Wildfire"), clock=lambda: FROZEN_NOW)

    package = adapter.fetch("EMSR842")

    assert package.verification_status is EvidenceStatus.CONFLICTING
    assert any(finding.severity is SourceVerificationSeverity.BLOCKER for finding in package.findings)


def test_cems_adapter_rejects_missing_activation() -> None:
    adapter = CemsActivationAdapter(http_get_json=lambda _url: {"count": 0, "results": []}, clock=lambda: FROZEN_NOW)

    with pytest.raises(SourceAdapterError, match="was not found"):
        adapter.fetch("EMSR999")


def _cems_payload(*, category: str) -> dict[str, object]:
    return {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "code": "EMSR927",
                "name": "Flood in Nepal",
                "reason": "Flash flood in Nepal with significant damage in Rasuwa District.",
                "category": category,
                "subCategory": "Flash flood",
                "sensitive": False,
                "eventTime": "2026-08-25T22:00:00",
                "activationTime": "2026-08-26T09:53:00",
                "closed": False,
                "countries": [{"name": "Nepal"}],
                "stats": {
                    "Roads [km]": 46,
                    "max_extent": 830,
                    "Population [No.]": 5300,
                    "Built-up area [ha]": 11,
                    "Identified buildings [No.]": 3207,
                },
                "charterNumber": "1052",
                "charterUrl": "https://disasterscharter.org/activations/flood-in-nepal-activation-1052-",
                "productsPath": "https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/EMSR927_products.zip",
                "aois": [
                    {
                        "number": 1,
                        "name": "Syapru Besi",
                        "products": [
                            {
                                "type": "GRA",
                                "feasible": True,
                                "expectedDelivery": "2026-08-27T20:00:00",
                                "downloadPath": "https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI01/GRA_PRODUCT.zip",
                                "version": {"statusCode": "F", "deliveryTime": "2026-08-27T19:03:49.982313"},
                            }
                        ],
                    },
                    {
                        "number": 2,
                        "name": "Timure",
                        "products": [
                            {
                                "type": "GRA",
                                "feasible": True,
                                "expectedDelivery": "2026-08-28T18:00:00",
                                "downloadPath": "https://rapidmapping.emergency.copernicus.eu/backend/EMSR927/AOI02/GRA_PRODUCT.zip",
                                "version": {"statusCode": "F", "deliveryTime": "2026-08-28T17:10:43.692032"},
                            }
                        ],
                    },
                    {
                        "number": 4,
                        "name": "Bharatpur",
                        "products": [
                            {
                                "type": "GRA",
                                "feasible": True,
                                "expectedDelivery": None,
                                "downloadPath": None,
                                "version": {"statusCode": "W", "deliveryTime": None},
                            }
                        ],
                    },
                ],
            }
        ],
    }
