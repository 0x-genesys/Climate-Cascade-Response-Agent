from __future__ import annotations

from datetime import UTC, datetime

from climate_cascade.domain import ImpactAnalysisStatus, VerifiedEvidencePackage
from climate_cascade.impacts import build_cems_product_impact_package


def test_cems_product_analysis_selects_latest_finished_product_and_extracts_operational_impacts() -> None:
    evidence = _evidence(_activation_payload())

    impacts = build_cems_product_impact_package(
        run_id="run-11111111-1111-4111-8111-111111111111", evidence=evidence
    )

    assert impacts.status is ImpactAnalysisStatus.COMPLETED
    assert len(impacts.aoi_impacts) == 2
    timure = next(aoi for aoi in impacts.aoi_impacts if aoi.aoi_name == "Timure")
    bidur = next(aoi for aoi in impacts.aoi_impacts if aoi.aoi_name == "Bidur")
    assert timure.population is not None
    assert timure.population.affected_population == 450
    assert timure.affected_residential_buildings == 225
    assert timure.access.affected_road_km == 5.4
    assert timure.access.affected_bridge_features == 1
    assert bidur.population is not None
    assert bidur.population.affected_population == 5000
    assert bidur.affected_residential_buildings == 3001
    assert bidur.access.affected_road_km == 37.1
    assert bidur.access.affected_bridge_features == 26
    assert "Power plant constructions" in {asset.asset_class.replace("Facilities: ", "") for asset in bidur.assets}
    assert any("Bharatpur" in gap for gap in impacts.data_gaps)
    assert "newest finished CEMS product" in impacts.deduplication_note


def test_cems_product_analysis_preserves_missing_raw_content_as_gap() -> None:
    evidence = _evidence(None)

    impacts = build_cems_product_impact_package(
        run_id="run-22222222-2222-4222-8222-222222222222", evidence=evidence
    )

    assert impacts.status is ImpactAnalysisStatus.INCOMPLETE
    assert impacts.aoi_impacts == []
    assert impacts.data_gaps == ["No raw CEMS activation snapshot is available for deterministic product-statistics analysis."]


def _evidence(raw_content: dict[str, object] | None) -> VerifiedEvidencePackage:
    snapshot: dict[str, object] = {
        "snapshot_id": "cems-emsr927-snapshot",
        "source_id": "cems-emsr927",
        "adapter": "cems-rapid-mapping",
        "publisher": "Copernicus Emergency Management Service",
        "source_url": "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?code=EMSR927",
        "retrieved_at": "2026-08-31T09:00:00Z",
        "kind": "raw_http_json",
        "content_sha256": "a" * 64,
        "content_type": "application/json",
        "license_note": "Public mapping source with citation required.",
    }
    if raw_content is not None:
        snapshot["raw_content"] = raw_content
    return VerifiedEvidencePackage.model_validate(
        {
            "package_id": "source-package-emsr927",
            "case_id": "emsr927",
            "activation_code": "EMSR927",
            "hazard_type": "flood_debris_flow",
            "verification_status": "preliminary",
            "retrieved_at": datetime(2026, 8, 31, 9, 0, tzinfo=UTC),
            "snapshots": [snapshot],
            "claims": [
                {
                    "claim_id": "cems-impact-stats",
                    "statement": "CEMS maps impact facts.",
                    "status": "supported",
                    "source_ids": ["cems-emsr927"],
                }
            ],
            "findings": [
                {
                    "finding_id": "cems-activation-open",
                    "severity": "warning",
                    "status": "preliminary",
                    "message": "The activation remains open.",
                    "source_ids": ["cems-emsr927"],
                }
            ],
        }
    )


def _activation_payload() -> dict[str, object]:
    return {
        "results": [
            {
                "aois": [
                    {
                        "number": 2,
                        "name": "Timure",
                        "products": [
                            {
                                "type": "GRA",
                                "stats": {
                                    "Estimated population": {"None": {"unit": "", "affected": 450}},
                                    "Built-up": {"Residential Buildings": {"unit": "", "affected": 225}},
                                    "Transportation": {
                                        "Primary Road": {"unit": "km", "affected": 5.4},
                                        "Bridges and elevated highways": {"unit": "", "affected": 1},
                                    },
                                },
                                "version": {"statusCode": "F", "number": 1, "deliveryTime": "2026-08-28T17:00:00"},
                            }
                        ],
                    },
                    {
                        "number": 3,
                        "name": "Bidur",
                        "products": [
                            {
                                "type": "GRA",
                                "stats": {"Estimated population": {"None": {"unit": "", "affected": 4400}}},
                                "version": {"statusCode": "F", "number": 1, "deliveryTime": "2026-08-29T02:00:00"},
                            },
                            {
                                "type": "GRA",
                                "stats": {
                                    "Estimated population": {"None": {"unit": "", "affected": 5000}},
                                    "Built-up": {"Residential Buildings": {"unit": "", "affected": 3001}},
                                    "Facilities": {"Power plant constructions": {"unit": "ha", "affected": 26.7}},
                                    "Transportation": {
                                        "Cart Track": {"unit": "km", "affected": 37.1},
                                        "Bridges and elevated highways": {"unit": "", "affected": 26},
                                    },
                                },
                                "version": {"statusCode": "F", "number": 1, "deliveryTime": "2026-08-31T01:00:00"},
                            },
                        ],
                    },
                    {
                        "number": 4,
                        "name": "Bharatpur",
                        "products": [{"type": "GRA", "version": {"statusCode": "W", "number": 1}}],
                    },
                ]
            }
        ]
    }
