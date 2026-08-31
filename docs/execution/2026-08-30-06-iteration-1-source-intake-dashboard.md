# Iteration 1 Source Intake and Dashboard

Date: 2026-08-30  
Sequence: 06  
ADR step: 6 - source adapters and Iteration 1 evidence contracts  
Status: implemented and source-intake verified

## Scope and acceptance criteria

Implement the first agent-mode stage without claiming action quality: retrieve a CEMS activation through a dedicated adapter, normalize it into a versioned evidence package, pin source metadata and a canonical SHA-256, retain AOI-product completeness and data gaps, persist it as an immutable run artifact, and surface it with durable run progress in a local dashboard.

Acceptance criteria:

- fixture and live CEMS source intake use the same typed `VerifiedEvidencePackage` contract
- each live package records the canonical public JSON payload plus source URL, publisher, retrieval time, content type, SHA-256, and license note
- open activations and waiting/in-production AOI products produce preliminary warnings and data gaps
- non-flood CEMS categories fail closed as outside the MVP
- agent runs move through `SOURCE_CHECK` and `VERIFIED`, then stop at `impact_analysis_pending` until Iteration 2 exists
- API tests cover agent creation, evidence retrieval, and static dashboard serving
- local shutdown on Ctrl-C returns cleanly

## Files changed

- `backend/src/climate_cascade/domain/models.py` and `domain/__init__.py`: source snapshot, CEMS activation/AOI, verification finding, and evidence-package contracts
- `backend/src/climate_cascade/sources/`: live CEMS adapter, frozen-fixture adapter, and workflow selection; the live adapter preserves the canonical public JSON payload with its hash
- `backend/src/climate_cascade/workflow/engine.py`: agent source-intake transitions and evidence artifact persistence
- `backend/src/climate_cascade/api/`: live agent-run validation, evidence endpoint, and dashboard serving
- `backend/src/climate_cascade/local.py`: dashboard-root option and clean Ctrl-C shutdown
- `dashboard/`: static source-intake and worker-progress view
- `backend/tests/test_source_adapters.py`, `backend/tests/test_workflow_api.py`, and `backend/tests/test_local_runtime.py`: contract, API, dashboard, and shutdown coverage

## Commands and verification

Focused checks:

```bash
uv run pytest backend/tests/test_local_runtime.py backend/tests/test_workflow_api.py backend/tests/test_source_adapters.py
uv run python -m compileall -q backend/src
uv lock --check
git diff --check
```

Result: `16 passed` in `0.64s`; compilation, lock check, and diff check passed. One existing FastAPI/Starlette `TestClient` deprecation warning was emitted.

Full suite:

```bash
uv run pytest
```

Result: `37 passed` in `0.57s`; the same upstream `TestClient` deprecation warning remained.

Live source-intake round:

```bash
uv run climate-cascade-local serve \
  --database-url sqlite:////tmp/climate-cascade-iteration1-evidence.db \
  --artifact-root /tmp/climate-cascade-iteration1-evidence-artifacts \
  --repository-root /Users/karanahuja/.treehouse/micro1_hackathon-9bf315/1/micro1_hackathon \
  --case-root /Users/karanahuja/.treehouse/micro1_hackathon-9bf315/1/micro1_hackathon/data/fixtures/cases \
  --dashboard-root /Users/karanahuja/.treehouse/micro1_hackathon-9bf315/1/micro1_hackathon/dashboard \
  --host 127.0.0.1 \
  --port 8025
```

The server response was checked at `/` and `/dashboard/app.js`. Three `POST /v1/agent/runs` requests then created live source-intake runs for `EMSR927`, `EMSR756`, and `EMSR851`; their terminal run status, stored evidence, and non-following SSE events were saved under `runs/iteration_1/`.

## Observed live-source results

| Activation | Event state | Source verification | AOI products | Data gaps | Workflow result |
| --- | --- | --- | --- | --- | --- |
| Nepal `EMSR927` | Open | `preliminary` | 5 | 2 | `blocked` at `impact_analysis_pending` |
| Poland `EMSR756` | Closed | `supported` | 35 | 0 | `blocked` at `impact_analysis_pending` |
| Sri Lanka `EMSR851` | Closed | `supported` | 29 | 0 | `blocked` at `impact_analysis_pending` |

Nepal's package records a reachable CEMS source, an open-activation warning, and a pending-product warning. It identifies Bidur and Bharatpur as waiting for data. Every saved live package now includes the raw public CEMS JSON payload alongside the canonical checksum. The completed historical activations establish that the adapter does not automatically label every CEMS source preliminary.

Machine-readable evidence: [summary](../../runs/iteration_1/iteration1-source-round-summary.json), [Nepal evidence](../../runs/iteration_1/nepal-emsr927-live-source.evidence.json), [Poland evidence](../../runs/iteration_1/poland-emsr756-live-source.evidence.json), and [Sri Lanka evidence](../../runs/iteration_1/sri-lanka-emsr851-live-source.evidence.json).

## Subsequent artifact-retention note

On 2026-08-31, the project owner requested removal of the static source-run artifacts named above. This historical execution record remains unchanged as a record of that earlier checkpoint, but those paths are no longer retained evidence. The current retained Iteration 1 bundle and final finding are documented in [record 15](2026-08-31-15-iteration-1-live-poc-finalization.md).

## Failures and corrections

- The first local server attempt used port `8021`, which was already occupied. It was rerun on `8023`; the final evidence-capture rerun used `8025` after raw snapshots were added.
- The initial test expected the wrong canonical-payload SHA-256. The expected checksum was updated to match the deterministic canonical JSON fixture.
- An initial Ctrl-C after the live run raised `KeyboardInterrupt` while joining the worker thread. `serve_local` now treats both the server interrupt and a second interrupt during join as clean local shutdown paths, with a regression test.
- The initial evidence package retained only a source hash and metadata. It now also persists the canonical public CEMS JSON payload, so the hash can be independently checked after the upstream activation changes.

After the shutdown correction, a local dashboard smoke run on port `8024` returned the dashboard title, `Worker Progress`, `Source Evidence`, and `{"status":"ready"}` from `/v1/health`. Ctrl-C exited the server with code `0` and no traceback.

## Evaluation boundary and decision

Keep the implementation. The run proves source status, completeness, snapshot provenance, persistence, and user-visible progress. It does not produce a response action, call a model, calculate an impact, or make a potential-lives-saved claim. Therefore it must not be presented as an LSAC@5 improvement, evidence-precision score, safety-rate result, or end-to-end emergency action workflow.

Next ADR step: implement deterministic population, asset, and access tools for Iteration 2. Only after typed actions exist should the project rerun the frozen human-adjudicated LSAC@5 comparison against the recorded baseline.

## Documentation updated

- `README.md`: dashboard and live source-intake commands, evaluation distinction, reviewer table, and repository layout
- `docs/product.md`: Iteration 1 implementation status and claim boundary
- `docs/architecture/ADR-0001-iterative-agentic-architecture.md`: static MVP dashboard decision and step-6 implementation status
- `docs/evaluation/README.md`: source-intake evaluation result and metric limits
- `docs/solution_improvement/README.md`: retained Iteration 1 finding
- `docs/story/README.md`: current demo beat and evidence-bound claim
