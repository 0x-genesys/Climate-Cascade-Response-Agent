# Local .env Loading

Date: 2026-08-31
Sequence: 08
ADR step: Reproducibility hardening for the local control plane
Status: implemented and verified

## Problem and acceptance criteria

The dashboard worker returned HTTP `401` after the user followed a prior shell example with the literal placeholder `your-key`. A reproducible local setup needs one clear place for the real key without exposing it in the dashboard or requiring an export in every new terminal.

Acceptance criteria:

- `.env` is ignored by Git and `.env.example` remains a safe committed template.
- Project CLI entry points load `.env` automatically when it exists.
- A missing `.env` remains valid for tests and no-key source workflows.
- An explicitly exported environment variable overrides `.env`.
- The key is never sent to the browser, stored in artifacts, or written to documentation as a real value.

## Implementation

- Added `python-dotenv` and `climate_cascade.environment.load_project_environment`.
- Invoked the loader at the baseline, evaluator, API server, worker, and combined local-server entry points before configuration is read.
- Added `.env` to `.gitignore` and updated `.env.example` and `README.md` with the one-time copy-and-edit workflow.
- Added focused tests for file loading, missing-file behavior, and exported-variable precedence.

## Verification

```bash
uv run pytest backend/tests/test_environment.py backend/tests/test_local_runtime.py
uv run pytest
uv lock --check
uv run python -m compileall -q backend/src
git diff --check
```

Result: focused environment and local-runtime checks reported `5 passed` in `0.51s`; the full suite reported `42 passed` in `0.70s`. `uv lock --check`, Python byte compilation, and `git diff --check` passed. `climate-cascade-local --help` and `climate-cascade-baseline --help` loaded after the dependency update. One existing FastAPI/Starlette `TestClient` deprecation warning remains.

## User workflow

```bash
cp .env.example .env
# Set OPENAI_API_KEY in .env to a real key, then:
uv run climate-cascade-local serve
```

No new agent-quality, safety, or benchmark metric is produced by this change.
