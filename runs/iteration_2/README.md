# Iteration 2 Live Nepal Product-Statistics POC

This directory retains the current Iteration 2 proof-of-concept evidence and one removed prompt-policy trajectory.

## Retained result

Run `run-f7fd675d-6370-4470-ac51-cc1356b7f581` used live CEMS `EMSR927`, response-supervisor configuration version `4`, and `gpt-5-mini-2025-08-07`.

- The worker selected one newest finished CEMS product per AOI, preventing duplicate version sums.
- It extracted source-reported population, residential buildings, facilities, roads, bridges, and the waiting Bharatpur-product gap into an immutable impact package.
- Five human-review-only drafts passed automatic checks: `0` unsafe autonomous-action findings, `0` missing evidence references, and `5` valid references.
- The authorized project-owner, AI-assisted rubric transfer measured LSAC@5 `13/17` (`76.47%`): Timure access, Bidur residential triage, and Bharatpur data handling were covered; Syapru Besi critical-services continuity was not.

## Claim boundary

This is not a fair comparison with the frozen baseline or Iteration 1. The source snapshot is live and mutable, the supervisor prompt and deterministic resource profile changed, and the reviewer is not credentialed emergency-management staff. The score is a diagnostic proof of location-specific drafting from product-level evidence, not a headline improvement claim.

## Files

- `nepal-emsr927-live-v4.run.json`: immutable response-supervisor trajectory.
- `nepal-emsr927-live-v4.evidence.json`: saved live CEMS source package.
- `nepal-emsr927-live-v4.impacts.json`: deterministic CEMS product-statistics impact package.
- `nepal-emsr927-live-v4.events.sse`: ordered worker event stream.
- `nepal-emsr927-live-v4.adjudication.json`: authorized project-owner coverage decisions.
- `nepal-emsr927-live-v4.evaluation.json`: deterministic rubric-transfer report.
- `removed/nepal-emsr927-live-v5-overcoverage.*`: the removed capacity-policy experiment that over-selected facility continuity and missed Timure access and Bharatpur data handling.

## Reproduce the deterministic score

The command below makes no model call:

```bash
uv run climate-cascade-evaluate-agent \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run runs/iteration_2/nepal-emsr927-live-v4.run.json \
  --evidence runs/iteration_2/nepal-emsr927-live-v4.evidence.json \
  --adjudication runs/iteration_2/nepal-emsr927-live-v4.adjudication.json \
  --evaluation-output runs/iteration_2/nepal-emsr927-live-v4.evaluation.json
```

See [the evaluation guide](../../docs/evaluation/agent.md) and [the finalization record](../../docs/execution/2026-08-31-16-iteration-2-live-poc-finalization.md).
