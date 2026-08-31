# Dashboard Glossary

- **Date and sequence:** 2026-08-31, record 13
- **Scope:** Reviewer-facing dashboard glossary
- **ADR step:** Keep the human review checkpoint comprehensible without weakening the bounded agent or evaluation boundary.

## Assumption and acceptance criteria

A reviewer seeing a successful draft run needs to distinguish source names, evidence controls, automatic checks, and the human LSAC@5 step. The dashboard should provide those definitions in one place, tied to the lifecycle stage where each is used.

The glossary must explain CEMS, USGS, International Charter, AOI, evidence snapshot, response supervisor, Draft only, Run Feedback, LSAC@5, human adjudication, `not estimable`, and SSE progress feed. It must remain readable on desktop and mobile.

## Files changed

- `dashboard/index.html`
- `dashboard/styles.css`
- `backend/tests/test_workflow_api.py`
- `docs/product.md`
- `docs/story/README.md`
- `docs/solution_improvement/README.md`

## Verification

```bash
uv run pytest backend/tests/test_workflow_api.py
uv run pytest
node --check dashboard/app.js
git diff --check
```

The focused dashboard/API suite reported `8 passed`; the full suite reported `46 passed`, each with one existing `starlette.testclient` deprecation warning. The static dashboard test verifies that the served page includes the glossary and the full LSAC@5 label. A local API-only smoke server on port `8011` returned the glossary labels and `/v1/health` returned `{"status":"ready"}`. JavaScript syntax and diff checks pass.

## Finding and decision

The latest credentialed Nepal run is successful at the automatic pre-review boundary: it reached `awaiting_human_review`, produced five drafts, and had zero unsafe autonomous-action findings and zero missing evidence references. Its LSAC@5 remains `not_evaluated` until a human completes the adjudication JSON, so this glossary does not claim any improvement over the baseline `3/17`.

Keep the glossary as demo and reviewer support. It makes the remaining human-evaluation step visible rather than implying that passing Run Feedback is a final quality score.
