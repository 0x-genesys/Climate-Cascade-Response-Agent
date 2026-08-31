# 2026-08-31-17 Live Baseline Comparison

ADR step: baseline-to-Iteration-2 fair-input comparison support.

## Change

The dashboard now selects real CEMS examples from a dropdown. A baseline can reuse a selected completed live agent run's immutable source evidence package. It receives raw saved CEMS evidence but no deterministic impact package. The response workflow receives the same source package plus the Iteration 2 impact artifact.

## Verification and Result

`uv run pytest -q` reported `51 passed` with one existing Starlette TestClient deprecation warning. `node --check dashboard/app.js` passed.

The first real baseline attempt failed closed because it cited raw CEMS-internal IDs rather than the permitted immutable snapshot ID. The prompt was corrected to state the exact allowed citation list; focused tests then passed.

Final paired source checksum: `1d0595d2121d9744de739ee6b41e77596ca9bf32ffb794a0cb7eddf448d9c8ca`.

- Agent `run-a50179a3-b497-41db-82df-92acfa0c8fa7`: five drafts, deterministic impacts, zero unsafe findings, zero missing references.
- Baseline `run-1403c22e-649d-4b63-a25e-a26996a96ff7`: five drafts, no impact package, zero unsafe findings, zero missing references.

Artifacts: `runs/live_comparison/2026-08-31-01-emsr927-*`.

## Decision

Keep the shared-snapshot path. Do not report an LSAC delta until a comparison rubric is frozen before the next pair and human coverage decisions are stored for both runs.
