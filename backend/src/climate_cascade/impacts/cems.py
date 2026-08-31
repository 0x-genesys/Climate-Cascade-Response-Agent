"""Derive compact, cited impact facts from CEMS product-level statistics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from climate_cascade.domain import (
    AccessImpact,
    AoiImpact,
    AssetImpact,
    ImpactAnalysisStatus,
    ImpactPackage,
    PopulationImpact,
    SourceSnapshot,
    VerifiedEvidencePackage,
)


def build_cems_product_impact_package(*, run_id: str, evidence: VerifiedEvidencePackage) -> ImpactPackage:
    """Use the newest finished product per AOI without inventing unavailable impact data."""

    snapshot = _cems_snapshot(evidence)
    if snapshot is None or not snapshot.raw_content:
        return _incomplete_package(
            run_id=run_id,
            evidence=evidence,
            gaps=["No raw CEMS activation snapshot is available for deterministic product-statistics analysis."],
        )
    activation = _activation(snapshot.raw_content)
    if activation is None:
        return _incomplete_package(
            run_id=run_id,
            evidence=evidence,
            gaps=["The saved CEMS activation snapshot has no parseable activation result."],
        )

    impacts: list[AoiImpact] = []
    gaps: list[str] = []
    for aoi in activation.get("aois", []):
        if not isinstance(aoi, dict):
            continue
        aoi_number = _as_int(aoi.get("number"))
        if aoi_number is None or aoi_number < 1:
            continue
        name = _text(aoi.get("name")) or f"AOI {aoi_number}"
        product = _newest_finished_product(aoi.get("products"))
        if product is None:
            gaps.append(f"{name} has no finished CEMS product with parseable impact statistics.")
            continue
        stats = product.get("stats")
        if not isinstance(stats, dict):
            gaps.append(f"{name} finished CEMS product has no impact statistics yet.")
            continue
        impacts.append(_aoi_impact(aoi_number, name, product, stats, snapshot.snapshot_id))

    status = ImpactAnalysisStatus.COMPLETED if impacts else ImpactAnalysisStatus.INCOMPLETE
    return ImpactPackage(
        package_id=f"impact-{evidence.package_id}",
        run_id=run_id,
        source_package_id=evidence.package_id,
        analysis_version="cems-product-stats-v1",
        status=status,
        analyzed_at=evidence.retrieved_at,
        aoi_impacts=impacts,
        data_gaps=gaps,
        deduplication_note=(
            "One newest finished CEMS product is selected per AOI by delivery time and version number; "
            "no duplicate product versions are summed. AOI population values remain source-reported aggregates."
        ),
    )


def _incomplete_package(*, run_id: str, evidence: VerifiedEvidencePackage, gaps: list[str]) -> ImpactPackage:
    return ImpactPackage(
        package_id=f"impact-{evidence.package_id}",
        run_id=run_id,
        source_package_id=evidence.package_id,
        analysis_version="cems-product-stats-v1",
        status=ImpactAnalysisStatus.INCOMPLETE,
        analyzed_at=evidence.retrieved_at,
        data_gaps=gaps,
        deduplication_note="No AOI population totals were calculated because no parseable CEMS product statistics were available.",
    )


def _cems_snapshot(evidence: VerifiedEvidencePackage) -> SourceSnapshot | None:
    return next((snapshot for snapshot in evidence.snapshots if snapshot.adapter == "cems-rapid-mapping"), None)


def _activation(raw_content: dict[str, Any]) -> dict[str, Any] | None:
    results = raw_content.get("results")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        return None
    return results[0]


def _newest_finished_product(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    candidates = [product for product in value if isinstance(product, dict) and _status(product) == "F"]
    return max(candidates, key=_product_sort_key) if candidates else None


def _product_sort_key(product: dict[str, Any]) -> tuple[str, int]:
    version = product.get("version") if isinstance(product.get("version"), dict) else {}
    return (str(version.get("deliveryTime") or ""), _as_int(version.get("number")) or 0)


def _aoi_impact(
    aoi_number: int, aoi_name: str, product: dict[str, Any], stats: dict[str, Any], snapshot_id: str
) -> AoiImpact:
    population = _sum_affected(stats.get("Estimated population"))
    residential = _affected_count(stats.get("Built-up"), "residential")
    assets = _asset_impacts(stats, snapshot_id)
    road_km, bridge_features = _transport_impacts(stats.get("Transportation"))
    access_status = "needs_human_verification" if road_km > 0 or bridge_features > 0 else "not_indicated"
    version = product.get("version") if isinstance(product.get("version"), dict) else {}
    return AoiImpact(
        aoi_number=aoi_number,
        aoi_name=aoi_name,
        product_type=_text(product.get("type")) or "unknown",
        product_delivery_time=_text(version.get("deliveryTime")),
        population=(
            PopulationImpact(
                affected_population=round(population),
                source_label="CEMS product Estimated population affected",
                deduplication_group=f"aoi-{aoi_number}-selected-product",
                evidence_ids=[snapshot_id],
            )
            if population is not None
            else None
        ),
        affected_residential_buildings=round(residential) if residential is not None else None,
        assets=assets,
        access=AccessImpact(
            affected_road_km=road_km,
            affected_bridge_features=round(bridge_features),
            status=access_status,
            evidence_ids=[snapshot_id],
        ),
        evidence_ids=[snapshot_id],
    )


def _asset_impacts(stats: dict[str, Any], snapshot_id: str) -> list[AssetImpact]:
    assets: list[AssetImpact] = []
    for category in ("Built-up", "Facilities"):
        entries = stats.get(category)
        if not isinstance(entries, dict):
            continue
        for asset_class, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            affected = _number(entry.get("affected"))
            if affected is None or affected <= 0:
                continue
            assets.append(
                AssetImpact(
                    asset_class=f"{category}: {asset_class}".strip(),
                    affected_value=affected,
                    unit=_text(entry.get("unit")) or "count_or_area",
                    evidence_ids=[snapshot_id],
                )
            )
    return assets


def _transport_impacts(value: object) -> tuple[float, float]:
    if not isinstance(value, dict):
        return 0.0, 0.0
    road_km = 0.0
    bridge_features = 0.0
    for label, entry in value.items():
        if not isinstance(entry, dict):
            continue
        affected = _number(entry.get("affected"))
        if affected is None:
            continue
        if "bridge" in str(label).lower():
            bridge_features += affected
        elif (_text(entry.get("unit")) or "").lower() == "km":
            road_km += affected
    return road_km, bridge_features


def _sum_affected(value: object) -> float | None:
    if not isinstance(value, dict):
        return None
    values = [_number(entry.get("affected")) for entry in value.values() if isinstance(entry, dict)]
    numeric = [item for item in values if item is not None]
    return sum(numeric) if numeric else None


def _affected_count(value: object, label_fragment: str) -> float | None:
    if not isinstance(value, dict):
        return None
    values = [
        _number(entry.get("affected"))
        for label, entry in value.items()
        if label_fragment in str(label).lower() and isinstance(entry, dict)
    ]
    numeric = [item for item in values if item is not None]
    return sum(numeric) if numeric else None


def _status(product: dict[str, Any]) -> str:
    version = product.get("version") if isinstance(product.get("version"), dict) else {}
    return str(version.get("statusCode") or "").upper()


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _as_int(value: object) -> int | None:
    return int(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None
