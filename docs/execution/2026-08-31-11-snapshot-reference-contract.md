# Snapshot Reference Contract and Rejected-Draft Feedback

Date: 2026-08-31
Sequence: 11
ADR step: Iteration 1 response-supervisor reliability repair
Status: implemented and verified

## Failure reproduced

Pinned Nepal run `run-842a402d-8296-4f29-b845-ec4fe7f5b0ff` returned four parseable draft actions but ended as `blocked` with:

```text
response references unknown evidence IDs:
['cems-activation-snapshot', 'charter-activation-snapshot', 'usgs-event-snapshot']
```

The supervisor prompt says to use IDs in `source_evidence.snapshots`; each snapshot exposes a durable `snapshot_id`, and the model correctly cited those values. The code incorrectly compared them with mutable source IDs instead. Because the response supervisor was not accepted, no deterministic evaluator report was stored. The dashboard nevertheless showed the response cards as ordinary drafts and left Run Feedback with a generic failure message.

## Repair

- Validate and deterministically evaluate supervisor action evidence against `SourceSnapshot.snapshot_id`.
- Preserve baseline evaluation against its frozen dossier source IDs; the baseline contract is not changed.
- Mark any response attached to a failed supervisor run as **Drafts rejected**, show the exact rejection above its cards, and surface the same detail in Run Feedback.

## Verification

```bash
uv run pytest backend/tests/test_response_supervisor.py backend/tests/test_workflow_api.py backend/tests/test_baseline_runner.py
uv run pytest
node --check dashboard/app.js
uv run python -m compileall -q backend/src
uv lock --check
git diff --check
```

Result: focused tests reported `19 passed` in `0.57s`; the full suite reported `45 passed` in `0.61s`. JavaScript syntax, Python byte compilation, lock validation, and whitespace checks passed. One existing FastAPI/Starlette `TestClient` deprecation warning remains.

The saved raw response from the failed Nepal run was validated locally against the corrected contract without an additional provider call. It contained four actions, no unknown snapshot IDs, and only `not_estimable` estimates.

## Evaluation boundary

The old run remains terminal and must not be scored because its stored supervisor artifact has `status: failed`. Start a fresh pinned Nepal run after deploying this repair. The dashboard will show automatic checks and the need for human review; the reviewer then completes the JSON adjudication and runs `climate-cascade-evaluate-agent` to calculate LSAC@5. No new quality score is claimed in this repair.
