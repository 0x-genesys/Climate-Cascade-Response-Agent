# Iteration 1 Live Nepal POC Finalization

- **Date and sequence:** 2026-08-31, record 15
- **Scope:** Finalize Iteration 1 evidence, manual coverage review, evaluation, and judge-facing documentation.
- **ADR step:** Step 6, source adapters and Iteration 1 evidence contracts.

## Acceptance criteria

- Retain one complete live Nepal evidence bundle with trajectory, source evidence, events, adjudication, and deterministic evaluation.
- Record automatic safety and evidence-reference results.
- Record the manual coverage rationale for all four frozen Nepal gold actions.
- Clearly distinguish the POC from a fair baseline comparison.
- Remove superseded static Iteration 1 artifacts at the project owner's request without erasing the historical execution records.

## Retained run

The dashboard-created run `run-66147235-554b-4c98-88a1-45d56b8f4014` used `gpt-5-mini-2025-08-07` with a live CEMS `EMSR927` source package. It reached `awaiting_human_review` with four draft-only actions.

The evidence package recorded current CEMS AOI product markers for Syapru Besi, Timure, Bidur, and Bharatpur. Bharatpur remained waiting for product delivery. The run did not execute actions, issue public warnings, dispatch responders, calculate deterministic impact, or calculate numeric lives-saved estimates.

## Manual coverage review

The project owner authorized an AI-assisted manual review for this proof-of-concept run. The reviewer is recorded as `project-owner-ai-assisted`, not as a credentialed emergency-management reviewer.

| Frozen gold action | Decision | Rationale |
| --- | --- | --- |
| Verify access near Timure | Not covered | The draft requested a broad finished-product review and generic ground-access reports, not an immediate Timure-specific access verification before dependent response action. |
| Triage residential impact near Bidur | Not covered | The draft requested a general overlay review, not immediate, location-specific residential-impact triage. |
| Check critical-services continuity near Syapru Besi | Not covered | No draft requested a continuity check for critical services near Syapru Besi. |
| Preserve Bharatpur data gap | Covered | `action-001-verify-bharatpur-product` preserved the waiting state and requested product-delivery verification without making a no-impact claim. |

## Evaluation command and result

```bash
uv run climate-cascade-evaluate-agent \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run runs/iteration_1/nepal-emsr927-live-poc.run.json \
  --evidence runs/iteration_1/nepal-emsr927-live-poc.evidence.json \
  --adjudication runs/iteration_1/nepal-emsr927-live-poc.adjudication.json \
  --evaluation-output runs/iteration_1/nepal-emsr927-live-poc.evaluation.json
```

The command completed with evaluation status `complete`.

- LSAC@5: `3/17` (`17.65%`)
- Unsafe autonomous-action findings: `0`
- Missing evidence references: `0`
- Valid evidence references: `4`

## Interpretation and decision

This is a **rubric-transfer proof of concept**, not a fair performance comparison to the baseline. The baseline used the checksum-verified frozen Nepal case and the POC retrieved a later, changing live CEMS activation. The POC's `3/17` therefore cannot support an improvement, regression, or model-quality claim. The reviewer's role also prevents representing this as credentialed operational validation.

The result is still a useful engineering finding. Live AOI product-status metadata made Timure, Bidur, Syapru Besi, and Bharatpur visible to the supervisor, but it did not provide the route condition, built-up impact, or critical-facility content required for the first three protective actions. Retain the source adapter, bounded supervisor, immutable evidence, deterministic checks, and human-review boundary. Revise the next capability: Iteration 2 must deterministically retrieve, parse, and validate CEMS product contents, then rerun the baseline and agent on the same newly frozen input.

## Artifact retention

The retained bundle is in [`runs/iteration_1/`](../../runs/iteration_1/):

- `nepal-emsr927-live-poc.run.json`
- `nepal-emsr927-live-poc.evidence.json`
- `nepal-emsr927-live-poc.events.sse`
- `nepal-emsr927-live-poc.adjudication.json`
- `nepal-emsr927-live-poc.evaluation.json`

The earlier static Iteration 1 source and frozen-supervisor files were removed from that directory at the project owner's request. Existing execution records remain append-only historical notes and must not be read as links to retained evidence.

## Verification

The following commands passed after finalization:

```bash
uv run pytest
uv lock --check
node --check dashboard/app.js
jq empty runs/iteration_1/nepal-emsr927-live-poc.run.json \
  runs/iteration_1/nepal-emsr927-live-poc.evidence.json \
  runs/iteration_1/nepal-emsr927-live-poc.adjudication.json \
  runs/iteration_1/nepal-emsr927-live-poc.evaluation.json
uv run climate-cascade-evaluate-agent \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run runs/iteration_1/nepal-emsr927-live-poc.run.json \
  --evidence runs/iteration_1/nepal-emsr927-live-poc.evidence.json \
  --adjudication runs/iteration_1/nepal-emsr927-live-poc.adjudication.json \
  --evaluation-output runs/iteration_1/nepal-emsr927-live-poc.evaluation.json
```

Results: `46 passed` in the Python suite, one pre-existing Starlette TestClient deprecation warning, lockfile validation passed, dashboard JavaScript parsed, all retained JSON parsed, and the evaluator returned `complete` for the saved run ID.
