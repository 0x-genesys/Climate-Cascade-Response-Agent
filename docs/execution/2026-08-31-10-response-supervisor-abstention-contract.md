# Response Supervisor Abstention Contract

Date: 2026-08-31
Sequence: 10
ADR step: Iteration 1 response-supervisor contract correction
Status: implemented and verified

## Failure and decision

After the validation-artifact serialization repair, the saved provider detail showed a safe model response pattern: action-level `LifeSafetyEstimate` objects with `status: "not_estimable"`, no numeric values, and concrete reasons explaining why impact or route evidence was insufficient.

The response supervisor was incorrectly using `BaselineActionResponse`, whose explicit fairness boundary forbids every estimate. This conflated the direct-prompt baseline rule with the Iteration 1 agent rule and rejected safe abstention. The baseline remains unchanged. The supervisor now uses a separate structured-output contract that allows only `not_estimable` abstentions and prohibits numeric estimates in its JSON schema and validation model.

## Implementation

- Added `NotEstimableLifeSafetyEstimate`, `ResponseSupervisorActionCandidate`, and `ResponseSupervisorActionResponse` contracts.
- Generated a separate strict response-supervisor schema whose estimate status is the literal `not_estimable`.
- Retained the baseline schema and its prohibition on every estimate.
- Updated the supervisor prompt to request either `null` or a reasoned `not_estimable` value.
- Rendered the abstention reason in the dashboard action card.

## Verification

```bash
uv run pytest backend/tests/test_response_supervisor.py backend/tests/test_baseline_runner.py backend/tests/test_workflow_api.py
uv run pytest
node --check dashboard/app.js
uv run python -m compileall -q backend/src
uv lock --check
git diff --check
```

Result: focused tests reported `19 passed` in `0.58s`; the full suite reported `45 passed` in `0.62s`. Tests assert that a response-supervisor abstention completes, a numeric estimate fails as `model_schema`, the baseline stays unestimated, and dashboard JavaScript contains the abstention display. One existing FastAPI/Starlette `TestClient` deprecation warning remains.

## Claim boundary

`not_estimable` is not an estimate, a life-saved claim, or deterministic impact analysis. It records visible abstention until Iteration 2 and Iteration 4 introduce the required geospatial impact and deterministic life-safety-calculator contracts. This repair has no human-adjudicated LSAC@5 result.
