"""Independent, deterministic review of a response-supervisor action draft."""

from __future__ import annotations

from enum import StrEnum
import re
from typing import Literal

from pydantic import Field

from climate_cascade.domain import ImpactPackage, NonEmptyText, ResponseSupervisorActionResponse, StrictModel, VerifiedEvidencePackage


class EvidenceSafetyVerdict(StrEnum):
    PASS = "pass"
    REVISE = "revise"
    REJECT = "reject"


class EvidenceSafetyFinding(StrictModel):
    code: NonEmptyText
    message: NonEmptyText
    action_id: str | None = None


class EvidenceSafetyReview(StrictModel):
    """A replayable verdict over observable draft content only."""

    schema_version: Literal["1"] = "1"
    run_id: str = Field(pattern=r"^run-[a-f0-9-]{36}$")
    verifier_id: Literal["evidence-safety-supervisor"] = "evidence-safety-supervisor"
    verifier_version: Literal["1"] = "1"
    verdict: EvidenceSafetyVerdict
    findings: list[EvidenceSafetyFinding]
    reviewed_action_count: int = Field(ge=0)
    known_evidence_ids: list[str]


_UNSAFE_TERMS = ("evacuate", "dispatch", "deploy", "public warning", "order residents")


def review_response_draft(
    *,
    run_id: str,
    response: ResponseSupervisorActionResponse,
    evidence: VerifiedEvidencePackage,
    impacts: ImpactPackage,
) -> EvidenceSafetyReview:
    """Validate citations, safety boundaries, and explicitly reported data gaps.

    This component receives the typed draft and public workflow inputs, not the
    response supervisor's prompt or provider output/reasoning.
    """

    known_evidence_ids = sorted(snapshot.snapshot_id for snapshot in evidence.snapshots)
    known_set = set(known_evidence_ids)
    findings: list[EvidenceSafetyFinding] = []
    action_text = " ".join(f"{action.title} {action.location_ref}".lower() for action in response.actions)

    for action in response.actions:
        unknown = sorted(set(action.evidence_ids) - known_set)
        if unknown:
            findings.append(
                EvidenceSafetyFinding(
                    code="unknown_evidence_reference",
                    action_id=action.action_id,
                    message=f"Action references evidence IDs not present in this run: {', '.join(unknown)}.",
                )
            )
        unsafe = next((term for term in _UNSAFE_TERMS if term in action.title.lower()), None)
        if unsafe:
            findings.append(
                EvidenceSafetyFinding(
                    code="unsafe_autonomous_action",
                    action_id=action.action_id,
                    message=f"Action contains disallowed autonomous language: {unsafe}.",
                )
            )

    # Reported data gaps must remain visible rather than silently disappearing
    # from the final review queue. The source phrase is used as the auditable key.
    for gap in impacts.data_gaps:
        if " has " not in gap:
            continue
        location = gap.split(" has ", 1)[0].strip()
        gap_terms = _gap_location_terms(location)
        visible_text = f"{action_text} {' '.join(response.limitations).lower()}"
        if gap_terms and not any(term in visible_text for term in gap_terms):
            findings.append(
                EvidenceSafetyFinding(
                    code="unaddressed_data_gap",
                    message=f"The explicit impact-analysis data gap for {location} is absent from actions and limitations.",
                )
            )

    if any(finding.code in {"unknown_evidence_reference", "unsafe_autonomous_action"} for finding in findings):
        verdict = EvidenceSafetyVerdict.REJECT
    elif findings:
        verdict = EvidenceSafetyVerdict.REVISE
    else:
        verdict = EvidenceSafetyVerdict.PASS
    return EvidenceSafetyReview(
        run_id=run_id,
        verdict=verdict,
        findings=findings,
        reviewed_action_count=len(response.actions),
        known_evidence_ids=known_evidence_ids,
    )


def _gap_location_terms(location: str) -> list[str]:
    """Accept either a CEMS AOI label or its human-readable place name."""

    terms = [location.lower()]
    terms.extend(value.strip().lower() for value in re.findall(r"\(([^)]+)\)", location))
    return [term for term in terms if term and term not in {"aoi", "area"}]
