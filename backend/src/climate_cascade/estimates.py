"""Deterministic Iteration 4 life-safety estimate boundary."""

from __future__ import annotations


def abstention_for_action(action_id: str) -> dict[str, object]:
    """Never invent a range until a reviewed parameter set is supplied."""

    return {
        "action_id": action_id,
        "status": "not_estimable",
        "low": None,
        "central": None,
        "high": None,
        "parameter_set_id": None,
        "abstention_reason": "No approved, hazard-specific life-safety parameter set is configured for this action.",
    }
