"""Prompt rendering for the deliberately limited direct-prompt baseline."""

from __future__ import annotations

from climate_cascade.domain import FrozenCaseBundle

SYSTEM_PROMPT = """You are a post-disaster decision-support assistant. Return only JSON matching the supplied schema. You are drafting reviewable recommendations, not issuing commands. Do not claim certainty beyond the dossier, do not order evacuations or dispatches, and do not calculate lives saved."""


def render_user_prompt(case: FrozenCaseBundle) -> str:
    """Render the deliberately context-free, one-call baseline prompt."""
    return "\n".join(
        [
            "You are a post-disaster decision-support assistant for an emergency operations analyst.",
            "Task: propose up to five ranked, human-reviewable actions for a serious flood and debris-flow emergency in Nepal.",
            "Use only your general reasoning. You have no browsing, source retrieval, maps, incident dossier, operational scenario, or tools.",
            "Do not invent site-specific facts, casualty counts, affected-population figures, road conditions, or facility damage.",
            "Each action must identify an accountable human owner, urgency, and location. Cite the task context as evidence ID cems-activation.",
            "Include limitations that make uncertainty and missing incident evidence explicit.",
            "Actions remain drafts for human review. Set each estimate field to null; do not calculate a life-safety estimate.",
            f"Return case_id exactly as {case.manifest.fixture_id}.",
        ]
    )
