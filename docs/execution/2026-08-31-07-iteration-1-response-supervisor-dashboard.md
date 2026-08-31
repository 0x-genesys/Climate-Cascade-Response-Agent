# Iteration 1 Response Supervisor and Review Dashboard

Date: 2026-08-31
Sequence: 07
ADR step: 6 - source adapters and Iteration 1 evidence contracts
Status: implemented and contract-verified; credentialed quality evaluation pending

## Why this continuation exists

The earlier Iteration 1 checkpoint ended after CEMS source intake. That was useful source evidence, but it did not complete the ADR's promised response-supervisor and evaluation path. This continuation restores the intended boundary without misrepresenting unimplemented impact analysis or spatial mapping as complete.

## Implementation

- Added `config/agents/response_supervisor.json` for a versioned, maximum-five-action supervisor policy.
- Added the response-supervisor runner and immutable trajectory artifact. It makes at most one structured request, excludes source `raw_content` and frozen gold actions from its prompt, and fails closed for missing configuration, provider error, schema failure, excessive actions, a mismatched case ID, or unknown evidence IDs.
- Extended the durable worker lifecycle from source evidence through `IMPACT_ANALYSIS` and `ACTION_DRAFTING` status events, response-supervisor drafting, deterministic evidence and safety checks, then `AWAITING_HUMAN_REVIEW`.
- Added a deterministic agent evaluator. It does not call a model and exposes LSAC@5 as `not_evaluated` until an explicit human coverage adjudication is supplied.
- Added `climate-cascade-evaluate-agent` plus [a manual adjudication guide](../evaluation/agent.md) and template.
- Added `GET /v1/runs` for the dashboard's previous-run dropdown and `GET /v1/runs/{run_id}/agent` for saved supervisor and evaluation artifacts.
- Redesigned the local dashboard as an incident briefing: guidance for a non-technical analyst, pinned and live input paths, sample CEMS activations, CEMS source documentation, official product links, an AOI availability schematic, source uncertainty, cited draft actions, deterministic check results, ordered run feedback, and reconnecting to prior runs.

## Verification

Focused response-supervisor, API, workflow, and dashboard-contract checks:

```bash
uv run pytest backend/tests/test_workflow_api.py backend/tests/test_response_supervisor.py
```

Result: `11 passed` in `0.52s`. One existing FastAPI/Starlette `TestClient` deprecation warning was emitted.

Full regression and static checks:

```bash
uv run pytest
node --check dashboard/app.js
uv run python -m compileall -q backend/src
uv lock --check
git diff --check
```

Result: `40 passed` after the dashboard API-contract correction. JavaScript syntax, Python byte compilation, lockfile validation, and whitespace checks passed. The only test warning is the upstream `TestClient` deprecation warning.

## Evaluation boundary

The static gateway exercises output contracts and deterministic checks. It is not a model-quality experiment. No credentialed response-supervisor run has been made during this checkpoint, no human adjudication exists for a supervisor draft, and no new LSAC@5, evidence precision, runtime, model cost, impact, or lives-saved claim is made.

The next evaluation action is deliberately manual and reproducible:

1. Start the local service with `OPENAI_API_KEY` set.
2. Run the pinned Nepal fixture from the dashboard with a structured-output model.
3. Save `/agent` and `/evidence` payloads, complete every decision in the adjudication template, and run `climate-cascade-evaluate-agent`.
4. Record the resulting machine-readable report and only then compare LSAC@5 with the `3/17` baseline.

## Product boundary

The dashboard's AOI view shows product availability and authoritative CEMS links. It is intentionally not a geographic map. Real CEMS geometry, population/asset/access calculations, and spatial overlays require the Iteration 2 deterministic impact contracts. The current action drafts are human-reviewable recommendations only: they cannot dispatch responders, issue warnings, approve actions, or claim lives saved.

## Documents updated

- `README.md`
- `docs/product.md`
- `docs/architecture/ADR-0001-iterative-agentic-architecture.md`
- `docs/evaluation/README.md` and `docs/evaluation/agent.md`
- `docs/solution_improvement/README.md`
- `docs/story/README.md`
