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

## Major Checkpoint Records

Treat a completed capability, contract/API/dashboard/workflow change, safety change, provider repair, benchmark run, or human adjudication as a major checkpoint. Close it only after updating the records that apply:

- `docs/execution/YYYY-MM-DD-NN-short-description.md` for every major code or evaluation checkpoint, with exact commands, tests, verification, artifacts, failures, decision, and a zero-padded same-day sequence in the filename.
- `docs/solution_improvement/README.md` for every major checkpoint, with final findings, metric or non-metric evidence, artifact links, decision, and learning. Make baseline and key-iteration findings easy to locate outside a wide table.
- `docs/evaluation/README.md` and the relevant evaluation guide after each completed or failed evaluation, with metric values, safety results, resources, artifact paths, and claim limits.
- `docs/story/README.md` after each measured evaluation, including the claims ledger and observed failure.
- `README.md` when reproducibility, setup, commands, artifacts, or benchmark status changes.
- Product and architecture records when scope, system design, safety boundaries, data, or implementation status changes.

## README discipline

Keep the root `README.md` aligned with the Micro1 submission guidance. It must introduce the intended user and bottleneck, explain the value and scope boundary, give clean-environment setup plus exact baseline, solution, and evaluation commands, identify required data and expected outputs, and state where secrets are supplied without committing them.

Update it whenever reproducibility inputs change. Link the improvement changelog, evaluation evidence, execution ledger, and trajectories. Do not present missing benchmark values, cost, runtime, or improvement as zero or as a completed result.

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
