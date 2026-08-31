"""Prompt rendering for the deliberately limited direct-prompt baseline."""

from __future__ import annotations

import json

from climate_cascade.domain import FrozenCaseBundle

SYSTEM_PROMPT = """You are a post-disaster decision-support assistant. Return only JSON matching the supplied schema. You are drafting reviewable recommendations, not issuing commands. Do not claim certainty beyond the dossier, do not order evacuations or dispatches, and do not calculate lives saved."""


def render_user_prompt(case: FrozenCaseBundle) -> str:
    """Flatten only frozen case facts and constraints into one model request."""

    dossier = case.dossier.model_dump(mode="json")
    scenario = case.scenario.model_dump(mode="json")
    return "\n".join(
        [
            "Create up to five ranked draft actions for the incident below.",
            "Each action must identify an accountable human owner, urgency, location, and source IDs from the dossier.",
            "Include limitations that preserve every data gap and uncertainty relevant to the recommendations.",
            "Actions remain drafts for human review. Set each estimate field to null; do not calculate a life-safety estimate.",
            "Incident dossier:",
            json.dumps(dossier, sort_keys=True, separators=(",", ":")),
            "Operational scenario:",
            json.dumps(scenario, sort_keys=True, separators=(",", ":")),
        ]
    )
