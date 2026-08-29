---
name: micro1-kickoff
description: "Prepare a Micro1 hackathon implementation plan after the prompt is released, with a baseline, an improved path, and proof strategy aligned to the judging rubric."
---

# Micro1 Kickoff

Use this skill when the task is to read the released hackathon prompt, turn it into a build plan, or choose what to implement first in this workspace.

Read [references/hackathon-brief.md](references/hackathon-brief.md) before making planning decisions.

## Outcome

Convert the prompt into a plan that is easy to execute and easy to score well.

The plan should explicitly define:

- the target user or workflow bottleneck
- the minimum baseline solution
- the improved solution
- the evidence or metrics that prove the improvement
- the reproduction path the judges will follow

## Working rules

- Start from the released prompt and tests, not from generic hackathon assumptions.
- Extract hard constraints first: required runtime, starter repo, API limits, evaluation environment, submission format, and any deterministic test requirements.
- Resolve ambiguity early. If the prompt allows multiple interpretations, choose the one that is easiest to prove correct and reproduce.
- Keep scope tight. A narrower project with a measurable delta is better than a broad system with weak evidence.
- Decide how the baseline will be implemented before designing the advanced path.

## Planning bias

- Prefer work that can produce a clear before and after comparison.
- Prefer deterministic checks, fixtures, or evaluation scripts over subjective claims.
- Prefer boring architecture over clever architecture unless the prompt rewards a specific advanced approach.
- Plan for the final README, changelog, and trajectories from the start rather than as cleanup.

## Minimum kickoff deliverable

Produce a short execution plan with:

1. exact prompt summary and constraints
2. baseline definition
3. improved solution definition
4. proof strategy and metrics
5. implementation order
6. top risks that could block scoring or reproducibility
