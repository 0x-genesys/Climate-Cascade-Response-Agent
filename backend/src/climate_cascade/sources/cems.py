"""Copernicus EMS Rapid Mapping source adapter."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

from climate_cascade.domain import (
    CemsActivationSummary,
    CemsAoiProductStatus,
    EvidenceClaim,
    EvidenceStatus,
    HazardType,
    SourceSnapshot,
    SourceSnapshotKind,
    SourceVerificationFinding,
    SourceVerificationSeverity,
    VerifiedEvidencePackage,
)


CEMS_ACTIVATION_ENDPOINT = "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/"
CEMS_LICENSE_NOTE = (
    "Copernicus EMS Rapid Mapping activation metadata is publicly accessible and must be cited as source data."
)
HttpGetJson = Callable[[str], dict[str, Any]]


class SourceAdapterError(RuntimeError):
    pass


class CemsActivationAdapter:
    def __init__(self, *, http_get_json: HttpGetJson | None = None, clock: Callable[[], datetime] | None = None) -> None:
        self._http_get_json = http_get_json or _http_get_json
        self._clock = clock or (lambda: datetime.now(UTC))

    def fetch(self, activation_code: str, *, case_id: str | None = None) -> VerifiedEvidencePackage:
        code = _normalize_activation_code(activation_code)
        source_url = f"{CEMS_ACTIVATION_ENDPOINT}?code={quote(code)}"
        retrieved_at = self._clock()
        payload = self._http_get_json(source_url)
        canonical_payload = _canonical_json(payload)
        payload_hash = sha256(canonical_payload.encode("utf-8")).hexdigest()
        results = payload.get("results")
        if not isinstance(results, list) or not results:
            raise SourceAdapterError(f"CEMS activation {code} was not found in the public activation API")
        activation = results[0]
        if not isinstance(activation, dict):
            raise SourceAdapterError(f"CEMS activation {code} returned an invalid activation object")
        source_id = f"cems-{code.lower()}"
        snapshot = SourceSnapshot(
            snapshot_id=f"{source_id}-snapshot",
            source_id=source_id,
            adapter="cems-rapid-mapping",
            publisher="Copernicus Emergency Management Service",
            source_url=source_url,
            retrieved_at=retrieved_at,
            kind=SourceSnapshotKind.RAW_HTTP_JSON,
            content_sha256=payload_hash,
            content_type="application/json",
            license_note=CEMS_LICENSE_NOTE,
            raw_content=payload,
        )
        summary = _activation_summary(code, activation)
        claims = _claims(source_id, summary)
        findings = _findings(source_id, summary)
        data_gaps = _data_gaps(summary)
        return VerifiedEvidencePackage(
            package_id=f"source-package-{code.lower()}",
            case_id=case_id or code.lower(),
            activation_code=code,
            hazard_type=_hazard_type(summary),
            verification_status=_package_status(summary, findings),
            retrieved_at=retrieved_at,
            snapshots=[snapshot],
            claims=claims,
            findings=findings,
            data_gaps=data_gaps,
            cems_activation=summary,
        )


def _http_get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=30) as response:
        if response.status >= 400:
            raise SourceAdapterError(f"CEMS API returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def _normalize_activation_code(value: str) -> str:
    code = value.strip().upper()
    if not code.startswith("EMSR") or not code[4:].isdigit() or len(code) != 7:
        raise SourceAdapterError(f"invalid CEMS activation code: {value!r}")
    return code


def _activation_summary(code: str, activation: dict[str, Any]) -> CemsActivationSummary:
    return CemsActivationSummary(
        activation_code=code,
        name=str(activation.get("name") or code),
        category=str(activation.get("category") or "Unknown"),
        sub_category=_optional_text(activation.get("subCategory")),
        event_time=_optional_text(activation.get("eventTime")),
        activation_time=_optional_text(activation.get("activationTime")),
        countries=_countries(activation.get("countries")),
        closed=bool(activation.get("closed")),
        report_link=_optional_url(activation.get("reportLink")),
        products_path=_optional_url(activation.get("productsPath")),
        charter_number=_optional_text(activation.get("charterNumber")),
        charter_url=_optional_url(activation.get("charterUrl")),
        stats=_stats(activation.get("stats")),
        aois=_aoi_products(activation.get("aois")),
    )


def _countries(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
        elif isinstance(item, str) and item:
            names.append(item)
    return names


def _stats(value: object) -> dict[str, str | int | float | bool]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, str | int | float | bool] = {}
    for key, item in value.items():
        if isinstance(item, str | int | float | bool):
            normalized[str(key)] = item
    return normalized


def _aoi_products(value: object) -> list[CemsAoiProductStatus]:
    if not isinstance(value, list):
        return []
    products: list[CemsAoiProductStatus] = []
    for aoi in value:
        if not isinstance(aoi, dict):
            continue
        aoi_number = int(aoi.get("number") or 0)
        aoi_name = str(aoi.get("name") or f"AOI {aoi_number}")
        for product in aoi.get("products") or []:
            if not isinstance(product, dict) or aoi_number < 1:
                continue
            version = product.get("version") if isinstance(product.get("version"), dict) else {}
            status_code = str(version.get("statusCode") or "UNKNOWN")
            products.append(
                CemsAoiProductStatus(
                    aoi_number=aoi_number,
                    aoi_name=aoi_name,
                    product_type=str(product.get("type") or "UNKNOWN"),
                    feasible=product.get("feasible") if isinstance(product.get("feasible"), bool) else None,
                    status_code=status_code,
                    status_label=_status_label(status_code),
                    delivery_time=_optional_text(version.get("deliveryTime")),
                    expected_delivery=_optional_text(product.get("expectedDelivery")),
                    download_path=_optional_url(product.get("downloadPath")),
                )
            )
    return products


def _claims(source_id: str, summary: CemsActivationSummary) -> list[EvidenceClaim]:
    claims = [
        EvidenceClaim(
            claim_id="cems-event-identity",
            statement=(
                f"CEMS activation {summary.activation_code} identifies {summary.name} as a "
                f"{summary.category}{' / ' + summary.sub_category if summary.sub_category else ''} event."
            ),
            status=EvidenceStatus.SUPPORTED,
            source_ids=[source_id],
        )
    ]
    if summary.stats:
        stat_text = ", ".join(f"{key}: {value}" for key, value in sorted(summary.stats.items()))
        claims.append(
            EvidenceClaim(
                claim_id="cems-impact-stats",
                statement=f"CEMS reports activation-level impact statistics: {stat_text}.",
                status=EvidenceStatus.SUPPORTED,
                source_ids=[source_id],
            )
        )
    if summary.aois:
        claims.append(
            EvidenceClaim(
                claim_id="cems-aoi-product-status",
                statement=(
                    f"CEMS lists {len(summary.aois)} AOI products: "
                    f"{summary.finished_product_count} finished and {summary.pending_product_count} waiting or in production."
                ),
                status=EvidenceStatus.SUPPORTED if summary.pending_product_count == 0 else EvidenceStatus.PRELIMINARY,
                source_ids=[source_id],
            )
        )
    return claims


def _findings(source_id: str, summary: CemsActivationSummary) -> list[SourceVerificationFinding]:
    findings = [
        SourceVerificationFinding(
            finding_id="cems-source-reachable",
            severity=SourceVerificationSeverity.INFO,
            status=EvidenceStatus.SUPPORTED,
            message=f"CEMS activation {summary.activation_code} was retrieved from the public Rapid Mapping API.",
            source_ids=[source_id],
        )
    ]
    if summary.category.lower() != "flood":
        findings.append(
            SourceVerificationFinding(
                finding_id="cems-hazard-outside-mvp",
                severity=SourceVerificationSeverity.BLOCKER,
                status=EvidenceStatus.CONFLICTING,
                message=f"CEMS category {summary.category!r} is outside the flood/debris-flow MVP.",
                source_ids=[source_id],
            )
        )
    if not summary.closed:
        findings.append(
            SourceVerificationFinding(
                finding_id="cems-activation-open",
                severity=SourceVerificationSeverity.WARNING,
                status=EvidenceStatus.PRELIMINARY,
                message="CEMS activation is still open, so AOIs, products, and statistics may change.",
                source_ids=[source_id],
            )
        )
    if summary.pending_product_count:
        findings.append(
            SourceVerificationFinding(
                finding_id="cems-products-pending",
                severity=SourceVerificationSeverity.WARNING,
                status=EvidenceStatus.PRELIMINARY,
                message=f"{summary.pending_product_count} AOI product(s) are waiting or still in production.",
                source_ids=[source_id],
            )
        )
    return findings


def _data_gaps(summary: CemsActivationSummary) -> list[str]:
    gaps = []
    for product in summary.aois:
        if product.status_code.upper() in {"W", "I"}:
            gaps.append(f"{product.aoi_name} {product.product_type} product is {product.status_label}.")
        if product.status_code.upper() == "F" and not product.download_path:
            gaps.append(f"{product.aoi_name} {product.product_type} product is finished but has no download path.")
    return gaps


def _hazard_type(summary: CemsActivationSummary) -> HazardType:
    return HazardType.FLOOD_DEBRIS_FLOW if summary.category.lower() == "flood" else HazardType.FLOOD_DEBRIS_FLOW


def _package_status(
    summary: CemsActivationSummary, findings: list[SourceVerificationFinding]
) -> EvidenceStatus:
    if any(finding.severity is SourceVerificationSeverity.BLOCKER for finding in findings):
        return EvidenceStatus.CONFLICTING
    if not summary.closed or summary.pending_product_count:
        return EvidenceStatus.PRELIMINARY
    return EvidenceStatus.SUPPORTED


def _status_label(status_code: str) -> str:
    return {
        "F": "finished",
        "W": "waiting for data",
        "I": "in production",
        "N": "not feasible or no visible impact",
    }.get(status_code.upper(), "unknown")


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_url(value: object) -> str | None:
    text = _optional_text(value)
    return text if text and text.startswith("https://") else None


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
