# Iteration 1 Live Nepal Proof of Concept

This directory contains the retained Iteration 1 evidence set.

## What this run proves

- A live CEMS EMSR927 retrieval passed source verification and exposed Syapru Besi, Timure, Bidur, and Bharatpur AOI product status to the response supervisor.
- The supervisor completed four draft-only actions with zero deterministic autonomous-action findings and zero missing evidence references.
- A project-owner, AI-assisted manual rubric review transferred the frozen Nepal action rubric to this live run and measured LSAC@5 at `3/17` (`17.65%`).

## What it does not prove

This is not the formal baseline comparison. The baseline used the older frozen Nepal source package, while this run used a newer live CEMS snapshot with changed statistics and AOI metadata. The manual review is not a credentialed emergency-management adjudication. The score is retained as a transparent proof-of-concept result, not claimed as measured improvement.

## Files

- nepal-emsr927-live-poc.run.json: immutable response-supervisor trajectory.
- nepal-emsr927-live-poc.evidence.json: saved live source package.
- nepal-emsr927-live-poc.events.sse: ordered worker event stream.
- nepal-emsr927-live-poc.adjudication.json: project-owner manual coverage decisions.
- nepal-emsr927-live-poc.evaluation.json: deterministic rubric-transfer score.

## Reproduce the deterministic score

The command below does not call a model. It checks the saved live trajectory against the saved evidence and manual decisions.

```bash
uv run climate-cascade-evaluate-agent \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run runs/iteration_1/nepal-emsr927-live-poc.run.json \
  --evidence runs/iteration_1/nepal-emsr927-live-poc.evidence.json \
  --adjudication runs/iteration_1/nepal-emsr927-live-poc.adjudication.json \
  --evaluation-output runs/iteration_1/nepal-emsr927-live-poc.evaluation.json
```

See [the evaluation guide](../../docs/evaluation/agent.md) for the comparison boundary and [the finalization record](../../docs/execution/2026-08-31-15-iteration-1-live-poc-finalization.md) for the full finding.
