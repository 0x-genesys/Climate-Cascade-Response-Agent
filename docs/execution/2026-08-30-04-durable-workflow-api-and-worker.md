# Durable Workflow, API, And Worker

Date: 2026-08-30
Sequence: 04

ADR steps: 3 - SQLite persistence and artifacts; 4 - FastAPI control API; 5 - leased worker workflow

## Objective

Build the durable local execution foundation that a dashboard and later agent workflow can use without losing run state, evidence, or user-visible progress.

## Implemented

- Alembic migration `0001_workflow_store` creates `runs`, `run_events`, `artifacts`, and `run_artifacts`.
- SQLite enables WAL, foreign keys, and a bounded busy timeout.
- The repository enforces idempotent run creation, monotonic per-run events, allowed state transitions, owned lease renewal and release, and expired-lease reclaim.
- `var/artifacts/sha256/...` stores canonical JSON and future binary artifacts by immutable digest.
- FastAPI exposes health, case listing, baseline and generic run creation, status, reconnectable SSE events, and saved baseline artifacts.
- A separate worker CLI atomically claims a run, persists every baseline stage, saves run and evaluation artifacts, and pauses at `awaiting_human_review`.
- Agent-mode runs are intentionally blocked because source verification is not implemented yet.

## Commands

```bash
uv sync --group dev
uv run pytest backend/tests/test_workflow_api.py
uv run pytest
```

For a local process demo:

```bash
uv run climate-cascade-api --database-url sqlite:///var/climate-cascade.db
uv run climate-cascade-worker --database-url sqlite:///var/climate-cascade.db
```

## Verification

- The first focused migration test failed because `migrations.ini` was absent from the worktree. Added the checked-in Alembic configuration and reran the test.
- The second focused run exposed SQLite's offset-naive datetime return. Lease ownership now normalizes stored timestamps to UTC before comparison.
- Focused tests then covered idempotency, migration, lease reclaim, worker progression, stored artifacts, API status, and SSE replay.
- Final verification: `uv run pytest` reported `26 passed in 0.46s`; `climate-cascade-api --help`, `climate-cascade-worker --help`, `uv lock --check`, and `git diff --check` passed. The test client emits one upstream FastAPI/Starlette deprecation warning about its `httpx` integration.
- Process smoke test: API on `127.0.0.1:8013` accepted a `POST /v1/baseline/runs`; a separate `climate-cascade-worker --once` leased it; `GET /v1/runs/{run_id}` returned `blocked` and `GET /v1/runs/{run_id}/baseline` returned persisted `provider_not_configured` run and evaluation artifacts. This was the expected fail-closed behavior with no `OPENAI_API_KEY`.
- No model-quality or agent-improvement evaluation occurred in this checkpoint. The saved Nepal baseline remains the only measured quality result.

## Decision

Keep this foundation. It provides durable, observable baseline execution and intentionally refuses to represent the unimplemented agent workflow as runnable. Iteration 1 now owns verified source adapters and AOI-specific evidence contracts.
