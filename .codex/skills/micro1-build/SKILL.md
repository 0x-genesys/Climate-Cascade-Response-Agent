---
name: micro1-build
description: "Build a Micro1 hackathon solution in this workspace with a strong baseline-to-improved progression, measurable evidence, reproducibility, and clean engineering."
---

# Micro1 Build

Use this skill when implementing or iterating on the hackathon project after the plan is set.

Read [references/hackathon-brief.md](references/hackathon-brief.md) before making major implementation decisions.

## Primary objective

Maximize score by producing a solution that is:

- correct enough to survive qualification checks
- easy to run from a clean environment
- clearly better than the baseline
- well evidenced

## Build order

1. Make the baseline real and runnable.
2. Add a repeatable evaluation path.
3. Implement the improved solution.
4. Re-run the same evaluation and capture the delta.
5. Tighten setup, docs, and failure handling as needed for reproducibility.

Do not jump straight to the advanced solution if it weakens the comparison or slows reproducibility.

## Decision criteria

- Favor maintainable, explicit code over agent-generated complexity.
- Keep functions and modules small enough that their behavior is easy to verify.
- Add error handling where missing behavior would break the demo, evaluation, or setup flow.
- Use stable fixtures, scripts, or sample data when the prompt allows it.
- If a feature is hard to prove, either simplify it or add better instrumentation.

## Evidence discipline

Maintain evidence while building:

- record exact commands used to run the baseline and improved paths
- record outputs, metrics, screenshots, or logs that support claims
- append meaningful iteration notes to the improvement changelog as the work evolves
- keep representative agent trajectories instead of trying to reconstruct them later

## Required implementation loop

For every meaningful build step:

1. Define acceptance criteria and focused tests before or alongside the change.
2. Run focused tests first, then the relevant full suite.
3. Verify user-visible, API, export, fixture, or trajectory behavior when applicable.
4. Record exact commands, outputs, failures, retries, runtime, environment, evidence paths, and the decision in `docs/execution/`.
5. Append the result to the improvement changelog and update product, evaluation, architecture, and story documentation when claims change.

Do not mark a step complete because code was written. A step is complete only after its tests, verification, and evidence record are complete.

## Avoid

- cosmetic changes presented as improvement
- fragile dependencies with no clear setup path
- hidden manual steps that judges would have to guess
- wide feature scope with no measurable success condition
- benchmarking that the judges cannot reproduce locally

## When the prompt is ambiguous

Choose the implementation that makes correctness and reproducibility easiest to demonstrate. State the assumption in the docs and keep the code consistent with it.
