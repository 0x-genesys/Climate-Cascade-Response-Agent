from __future__ import annotations

import pytest
from pydantic import ValidationError

from climate_cascade.domain import (
    ActionCandidate,
    ActionUrgency,
    EvidenceStatus,
    LifeSafetyEstimate,
    LifeSafetyStatus,
    ReviewDecision,
    ReviewDecisionType,
    SourceReference,
)


def test_estimated_life_safety_range_requires_ordered_values_and_provenance() -> None:
    estimate = LifeSafetyEstimate(
        action_id="verify-access-timure",
        status=LifeSafetyStatus.ESTIMATED,
        low=1.0,
        central=2.0,
        high=3.0,
        parameter_set_id="synthetic-flood-v1",
        population_deduplication_group="timure-access-v1",
    )

    assert estimate.central == 2.0

    with pytest.raises(ValidationError, match="low <= central <= high"):
        LifeSafetyEstimate(
            action_id="verify-access-timure",
            status=LifeSafetyStatus.ESTIMATED,
            low=3.0,
            central=2.0,
            high=1.0,
            parameter_set_id="synthetic-flood-v1",
            population_deduplication_group="timure-access-v1",
        )


def test_not_estimable_life_safety_result_requires_a_reason_and_no_numbers() -> None:
    estimate = LifeSafetyEstimate(
        action_id="verify-access-timure",
        status=LifeSafetyStatus.NOT_ESTIMABLE,
        abstention_reason="No approved flood fatality-risk parameter set is available for this case.",
    )

    assert estimate.status == LifeSafetyStatus.NOT_ESTIMABLE

    with pytest.raises(ValidationError, match="cannot include numeric estimates"):
        LifeSafetyEstimate(
            action_id="verify-access-timure",
            status=LifeSafetyStatus.NOT_ESTIMABLE,
            low=1.0,
            abstention_reason="No approved parameter set is available.",
        )


def test_action_rejects_an_estimate_for_another_action() -> None:
    estimate = LifeSafetyEstimate(
        action_id="different-action",
        status=LifeSafetyStatus.NOT_ESTIMABLE,
        abstention_reason="No approved parameter set is available.",
    )

    with pytest.raises(ValidationError, match="must match action_id"):
        ActionCandidate(
            action_id="verify-access-timure",
            title="Verify access to affected communities near Timure.",
            location_ref="aoi:timure",
            owner_role="incident_commander",
            urgency=ActionUrgency.IMMEDIATE,
            evidence_ids=["cems-activation"],
            estimate=estimate,
        )


def test_source_references_require_timezone_aware_retrieval_times() -> None:
    with pytest.raises(ValidationError, match="must include a timezone"):
        SourceReference(
            source_id="cems-activation",
            publisher="Copernicus Emergency Management Service",
            source_url="https://example.test/source",
            retrieved_at="2026-08-29T15:47:06",
            materialization="curated_summary",
            license_note="Publicly accessible source used in a fixture.",
        )


def test_domain_contracts_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SourceReference(
            source_id="cems-activation",
            publisher="Copernicus Emergency Management Service",
            source_url="https://example.test/source",
            retrieved_at="2026-08-29T15:47:06Z",
            materialization="curated_summary",
            license_note="Publicly accessible source used in a fixture.",
            unsupported_field=True,
        )


def test_review_decision_requires_a_meaningful_human_rationale() -> None:
    with pytest.raises(ValidationError, match="at least 10 characters"):
        ReviewDecision(
            action_id="verify-access-timure",
            decision=ReviewDecisionType.REQUEST_EVIDENCE,
            reviewer_id="demo-commander",
            reviewer_role="incident commander",
            rationale="Too short",
            decided_at="2026-08-29T15:47:06Z",
        )


def test_evidence_status_is_a_closed_enum() -> None:
    assert EvidenceStatus.PRELIMINARY.value == "preliminary"
