# Dashboard Review Flow

- **Date and sequence:** 2026-08-31, record 19
- **Scope:** replace the pinned dashboard fixture entry point with named live CEMS examples, clarify source-coverage presentation, reorder supporting impact information, and make persisted human-review decisions visible in the action queue.

## Implementation

The dashboard now provides named `EMSR927` Nepal, `EMSR756` South-west Poland, and `EMSR851` Sri Lanka live CEMS examples. A separate CEMS activation selector includes the same supported codes and a short table explaining what each example is useful for. Both controls create live agent runs; no dashboard button starts a fixture run.

The former `Official mapping` presentation is now `Source coverage`. A green card means CEMS delivered a product whose facts can support the downstream impact panel. An amber card means the product is still awaited and the system must not infer impacts. Deterministic impact analysis is now placed after the human review queue as supporting information.

The action renderer consumes `/v1/runs/{run_id}/actions`, selects the newest version for each persisted review, and updates the matching action status from `Draft only` to the recorded human decision. The review form now exposes clear labels, a recorded-count indicator, reviewer identity and role fields, a rationale field, and the safe `not_estimable` limitation.

## Verification

```bash
uv run pytest backend/tests/test_workflow_api.py
node --check dashboard/app.js
uv run pytest
uv run climate-cascade-local init --database-url sqlite:///var/dashboard-smoke.db --artifact-root var/dashboard-smoke-artifacts
uv run climate-cascade-api --database-url sqlite:///var/dashboard-smoke.db --artifact-root var/dashboard-smoke-artifacts --port 8006
curl -fsS http://127.0.0.1:8006/v1/health
```

- Focused workflow/API test: `10 passed`.
- Full suite: `54 passed`, with the existing Starlette `TestClient` deprecation warning.
- JavaScript syntax and diff whitespace checks passed.
- Local browser smoke check confirmed one Flood examples selector, one Live CEMS activation selector, exactly one `Run` button, no remaining pinned-practice text, the new CEMS coverage title, and no console errors.
- Mobile smoke check at `390px` found no horizontal overflow.

## Result And Limit

This is a dashboard and auditability improvement. It does not create a new LSAC evaluation or change the retained Iteration 4 live transfer score of `13/17`. A recorded decision remains a non-executing audit record; request-evidence and edit decisions do not yet route a run back through the workflow.
