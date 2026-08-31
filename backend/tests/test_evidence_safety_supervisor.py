from __future__ import annotations

from pathlib import Path

from climate_cascade.agents import EvidenceSafetyVerdict, review_response_draft
from climate_cascade.domain import ResponseSupervisorActionResponse, load_frozen_case
from climate_cascade.impacts import build_cems_product_impact_package
from climate_cascade.sources import build_fixture_evidence_package


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CASE = load_frozen_case(REPOSITORY_ROOT / "data" / "fixtures" / "cases" / "nepal-emsr927-v1")
RUN_ID = "run-55555555-5555-4555-8555-555555555555"


def test_verifier_requests_revision_when_an_explicit_gap_is_hidden() -> None:
    evidence = build_fixture_evidence_package(CASE)
    impacts = build_cems_product_impact_package(run_id=RUN_ID, evidence=evidence).model_copy(
        update={"data_gaps": ["Bharatpur has no finished CEMS product with parseable impact statistics."]}
    )
    response = _response(evidence_id="cems-activation-snapshot")
    response["actions"] = response["actions"][:1]
    response["actions"][0]["title"] = "Ask for a Timure access verification"
    response["actions"][0]["location_ref"] = "Timure AOI"
    response["limitations"] = ["Some official product information remains incomplete."]

    review = review_response_draft(
        run_id=RUN_ID,
        response=ResponseSupervisorActionResponse.model_validate(response),
        evidence=evidence,
        impacts=impacts,
    )

    assert review.verdict is EvidenceSafetyVerdict.REVISE
    assert {finding.code for finding in review.findings} == {"unaddressed_data_gap"}


def test_verifier_rejects_unknown_citations_and_autonomous_language() -> None:
    evidence = build_fixture_evidence_package(CASE)
    impacts = build_cems_product_impact_package(run_id=RUN_ID, evidence=evidence)
    response = _response(evidence_id="unknown-evidence")
    response["actions"][0]["title"] = "Dispatch a field team to Timure immediately"

    review = review_response_draft(
        run_id=RUN_ID,
        response=ResponseSupervisorActionResponse.model_validate(response),
        evidence=evidence,
        impacts=impacts,
    )

    assert review.verdict is EvidenceSafetyVerdict.REJECT
    assert {"unknown_evidence_reference", "unsafe_autonomous_action"} <= {
        finding.code for finding in review.findings
    }


def _response(*, evidence_id: str) -> dict[str, object]:
    return {
        "schema_version": "1",
        "case_id": CASE.manifest.fixture_id,
        "actions": [
            {
                "schema_version": "1",
                "action_id": "request-bharatpur-evidence",
                "title": "Request pending Bharatpur map evidence before deciding impact",
                "location_ref": "Bharatpur AOI",
                "owner_role": "emergency operations analyst",
                "urgency": "monitor",
                "evidence_ids": [evidence_id],
                "status": "draft",
                "estimate": None,
            }
        ],
        "limitations": ["Bharatpur has no finished CEMS product with parseable impact statistics."],
    }
