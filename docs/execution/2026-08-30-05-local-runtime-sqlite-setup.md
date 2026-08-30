# Local Runtime SQLite Setup

Date: 2026-08-30  
Sequence: 05  
ADR step: reproduction hardening for steps 3-5  
Branch: `agent_build_1`

## Scope

The durable workflow foundation had API and worker commands, but the clean local setup path was incomplete:

- no focused test covered the user-facing local SQLite initialization command
- the persistence layer did not guarantee parent-directory creation before opening a file-backed SQLite database
- the README showed separate API and worker commands, but not a single `uv run` command that prepares the local database and brings up the server plus worker together

This checkpoint does not change the baseline prompt, evaluation rubric, adjudication labels, agent workflow, or LSAC@5 result.

## Acceptance Criteria

- `uv run climate-cascade-local init` creates the local SQLite database, applies migrations, and prepares the artifact directory.
- `uv run climate-cascade-local serve` starts the FastAPI API and a local worker against the same SQLite database and artifact root.
- File-backed SQLite URLs create missing parent directories before connection and migration.
- Tests cover the local setup and startup wiring.
- README and solution-improvement evidence list the exact `uv run` setup/start commands.

## Files Changed

- `backend/src/climate_cascade/persistence/database.py`
- `backend/src/climate_cascade/local.py`
- `backend/tests/test_local_runtime.py`
- `pyproject.toml`
- `.env.example`
- `README.md`
- `docs/product.md`
- `docs/architecture/ADR-0001-iterative-agentic-architecture.md`
- `docs/solution_improvement/README.md`
- `docs/execution/2026-08-30-05-local-runtime-sqlite-setup.md`

## Fixture and Configuration Versions

- Fixture: `data/fixtures/cases/nepal-emsr927-v1`
- Database default: `sqlite:///var/climate-cascade.db`
- Artifact default: `var/artifacts`
- API default: `127.0.0.1:8000`
- Model provider: unchanged; no model call was made

## Commands and Results

Focused tests:

```bash
uv run pytest backend/tests/test_local_runtime.py
```

Result after final metadata rebuild: `2 passed, 1 warning in 0.35s`. The warning is the existing upstream FastAPI/Starlette `TestClient` deprecation related to `httpx`.

Full suite:

```bash
uv run pytest
```

Result after final metadata rebuild: `28 passed, 1 warning in 0.49s`.

Lock verification:

```bash
uv lock --check
```

Result: passed.

Metadata rebuild:

```bash
uv run python -m pip install -e .
```

Result: failed because the `uv` virtual environment does not include a `pip` module.

```bash
uv pip install -e .
```

Result: passed and regenerated the tracked package metadata for the new `climate-cascade-local` console script and updated product long description.

Local command help:

```bash
uv run climate-cascade-local --help
```

Result: passed and exposed `init` plus `serve` subcommands.

Local SQLite initialization:

```bash
uv run climate-cascade-local init \
  --database-url sqlite:////tmp/climate-cascade-local-test-final.db \
  --artifact-root /tmp/climate-cascade-local-artifacts-final \
  --repository-root /Users/karanahuja/.treehouse/micro1_hackathon-9bf315/1/micro1_hackathon
```

Result: passed. Alembic applied migration `0001_workflow_store` and printed:

```text
initialized database=sqlite:////tmp/climate-cascade-local-test-final.db artifacts=/tmp/climate-cascade-local-artifacts-final
```

Local server smoke:

```bash
uv run climate-cascade-local serve \
  --database-url sqlite:////tmp/climate-cascade-local-smoke-8016.db \
  --artifact-root /tmp/climate-cascade-local-smoke-artifacts-8016 \
  --repository-root /Users/karanahuja/.treehouse/micro1_hackathon-9bf315/1/micro1_hackathon \
  --case-root /Users/karanahuja/.treehouse/micro1_hackathon-9bf315/1/micro1_hackathon/data/fixtures/cases \
  --host 127.0.0.1 \
  --port 8016 \
  --worker-once
```

Health check:

```bash
curl -s http://127.0.0.1:8016/v1/health
```

Result:

```json
{"status":"ready"}
```

The smoke-test server was stopped with `Ctrl-C` after the health check.

Compile check:

```bash
uv run python -m compileall -q backend/src
```

Result: passed.

## Primary Checkout Verification

After pushing commit `0bc49f5`, the primary checkout was fast-forwarded and the user-facing install/startup path was rerun from `/Users/karanahuja/AI_Workload/micro1_hackathon`.

Install:

```bash
uv sync --group dev
```

Result: passed and installed `climate-cascade-response==0.1.0` from the primary checkout.

Full suite:

```bash
uv run pytest
```

Result: `28 passed, 1 warning in 1.88s`.

Local command help:

```bash
uv run climate-cascade-local --help
```

Result: passed.

Local SQLite initialization:

```bash
uv run climate-cascade-local init \
  --database-url sqlite:////tmp/climate-cascade-primary-local-test.db \
  --artifact-root /tmp/climate-cascade-primary-local-artifacts \
  --repository-root /Users/karanahuja/AI_Workload/micro1_hackathon
```

Result: passed and applied migration `0001_workflow_store`.

Local server smoke:

```bash
uv run climate-cascade-local serve \
  --database-url sqlite:////tmp/climate-cascade-primary-local-smoke-8017.db \
  --artifact-root /tmp/climate-cascade-primary-local-smoke-artifacts-8017 \
  --repository-root /Users/karanahuja/AI_Workload/micro1_hackathon \
  --case-root /Users/karanahuja/AI_Workload/micro1_hackathon/data/fixtures/cases \
  --host 127.0.0.1 \
  --port 8017 \
  --worker-once
```

Health check:

```bash
curl -s http://127.0.0.1:8017/v1/health
```

Result:

```json
{"status":"ready"}
```

The primary smoke-test server was stopped with `Ctrl-C` after the health check.

## Implementation Notes

- `ensure_sqlite_parent()` now creates the parent directory for non-memory SQLite database URLs before `create_engine()` and before Alembic migrations.
- `climate-cascade-local init` prepares local runtime state without starting a long-running process.
- `climate-cascade-local serve` prepares the runtime, starts the API, and starts a worker thread unless `--no-worker` is supplied.
- The combined local command runs migrations once, then builds the API and worker against that prepared runtime.
- `--worker-once` exists for smoke tests and controlled local validation; normal demo use should omit it.

## Failures and Deviations

- `uv run python -m pip install -e .` failed because the local `uv` environment has no `pip` module. `uv pip install -e .` succeeded and is the correct metadata rebuild command here.
- The local server smoke did not create or process a run. It verified process startup and API health only.
- Temporary `/tmp` SQLite and artifact paths were used for smoke checks to avoid modifying reviewer-facing `var/` artifacts during validation.

## Documentation Updates

- `README.md` now includes `uv sync --group dev`, `uv run climate-cascade-local init`, `uv run climate-cascade-local serve`, separate API/worker alternatives, health-check guidance, and the local runtime evidence link.
- `docs/solution_improvement/README.md` now has a dedicated local-runtime reproducibility row.
- `docs/product.md` and the ADR implementation status now mention the local `uv run` setup/startup path.

## Decision

Keep this change. It converts local SQLite setup and server startup from implicit operational knowledge into a tested, reviewer-facing command path.

## Next Step

Continue ADR step 6: implement source adapters and Iteration 1 evidence contracts, then rerun the same frozen evaluation once the workflow can produce improved actions.
