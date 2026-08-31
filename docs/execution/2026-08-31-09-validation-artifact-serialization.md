# Validation Artifact Serialization Repair

Date: 2026-08-31
Sequence: 09
ADR step: Iteration 1 response-supervisor reliability repair
Status: implemented and verified

## Failure reproduced

Dashboard run `run-390c7aec-b6f3-412d-a271-193b10950219` reached `ACTION_DRAFTING`, then ended as:

```text
Workflow blocked by TypeError: Object of type ValueError is not JSON serializable
```

The model response had reached Pydantic validation. When a model-level validator raises `ValueError`, Pydantic keeps that exception in `error.errors()[...]["ctx"]["error"]`. The compact error formatter then attempted a normal `json.dumps`, which failed before the response-supervisor artifact could be stored. The outer workflow safety handler correctly blocked the run, but it could only show the secondary serialization failure.

## Repair

- Serialize validation-error context with `default=str` in both the response-supervisor and direct-baseline compact error formatters.
- Added regression tests using duplicate action IDs, which trigger the same Pydantic `ValueError` context.

The expected user-visible behavior is now a normal `response_supervisor_failed` event and a stored `response_supervisor_run` artifact with `failure_code: "model_schema"` and the original validation detail. No invalid action proceeds to human review.

## Verification

```bash
uv run pytest backend/tests/test_response_supervisor.py backend/tests/test_baseline_runner.py
uv run pytest
node --check dashboard/app.js
uv run python -m compileall -q backend/src
uv lock --check
git diff --check
```

Result: focused tests reported `10 passed` in `0.26s`; the full suite reported `44 passed` in `0.72s`. JavaScript syntax, Python byte compilation, lock validation, and whitespace checks passed. One existing FastAPI/Starlette `TestClient` deprecation warning remains.

## Decision

Keep. The repair preserves the actual provider-output contract failure for the user and evaluator, instead of masking it with an internal serialization exception. It does not change the agent prompt, source evidence, evaluation score, or safety policy.
