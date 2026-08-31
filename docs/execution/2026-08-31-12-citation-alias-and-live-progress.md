# Citation Alias and Live Progress Repair

- **Date and sequence:** 2026-08-31, record 12
- **Scope:** Iteration 1 response-supervisor citation compatibility and dashboard workflow visibility
- **ADR step:** Preserve typed evidence contracts and durable SSE trajectory while keeping the response supervisor bounded.

## Failure and acceptance criteria

The newest local Nepal practice run, `run-15868334-abd9-4f7c-b426-c86875f7f0b9`, stopped at `blocked` with `output_policy`. Its stored model response cited the valid source aliases `cems-activation`, `usgs-event`, and `charter-activation`; the prior validator only accepted immutable snapshot IDs such as `cems-activation-snapshot`.

The repair must:

1. retain the raw provider response but persist accepted action citations only as immutable snapshot IDs;
2. accept only a known source-ID to snapshot-ID alias, and still reject unknown IDs;
3. tell the model the exact allowed snapshot IDs;
4. append durable SSE `working` events before source intake, model drafting, receipt of a structured response, and deterministic checks; and
5. show the received SSE message in the dashboard without claiming token streaming or private reasoning.

## Files changed

- `backend/src/climate_cascade/agents/response_supervisor.py`
- `backend/src/climate_cascade/persistence/repositories.py`
- `backend/src/climate_cascade/workflow/engine.py`
- `backend/tests/test_response_supervisor.py`
- `backend/tests/test_workflow_api.py`
- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/styles.css`
- `docs/evaluation/agent.md`
- `docs/product.md`
- `docs/architecture/ADR-0001-iterative-agentic-architecture.md`
- `docs/story/README.md`
- `docs/solution_improvement/README.md`

## Verification

Focused contract and API tests:

```bash
uv run pytest backend/tests/test_response_supervisor.py backend/tests/test_workflow_api.py
```

Result: `14 passed` with one existing `starlette.testclient` deprecation warning.

Full regression verification:

```bash
uv run pytest
```

Result: `46 passed` with the same existing deprecation warning.

The static-worker API smoke created a pinned Nepal agent run whose model response used `cems-activation` and `charter-activation` source aliases. The run reached `awaiting_human_review`; the persisted action cited `cems-activation-snapshot` and `charter-activation-snapshot`; the SSE replay included `source_intake_started`, `response_supervisor_started`, `response_supervisor_response_received`, and `draft_checks_started`.

The exact raw provider response from rejected local run `run-15868334-abd9-4f7c-b426-c86875f7f0b9` was replayed against the repaired contract without making a provider call. It completed and its citations normalized to `cems-activation-snapshot`, `usgs-event-snapshot`, and `charter-activation-snapshot`.

Additional checks:

```bash
node --check dashboard/app.js
uv run python -m compileall -q backend/src
uv lock --check
git diff --check
```

All passed.

## Findings and decision

The provider can choose a source alias despite an exact-ID instruction because both identifier types occur in compact evidence. Canonicalizing only known aliases at the typed supervisor boundary preserves a stable immutable citation contract and does not allow arbitrary references.

The dashboard now reports observable operations over its existing ordered SSE channel. It intentionally does not show fabricated phrases such as model "thinking" or unvalidated partial model text. This is a reliability and observability repair, not an agent-quality evaluation. The Nepal response supervisor still needs a fresh credentialed run and human adjudication before it can be compared with the baseline LSAC@5 `3/17`.
