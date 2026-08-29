# Domain Schemas and Frozen Case Execution

Date: 2026-08-29  
Status: Complete  
ADR step: `1. Define domain schemas and frozen case format`

## Scope

Define versioned Pydantic contracts for the baseline and later workflow, then add a checksum-verified Nepal `EMSR927` baseline fixture.

## Assumption

The direct-prompt baseline needs a stable, cited input dossier before live source verification exists. A curated summary is acceptable only when it is explicitly marked as such, integrity-protected, and separated from synthetic operational constraints.

## Acceptance criteria

- Domain models reject unknown fields, invalid timestamps, invalid life-safety ranges, and broken review requirements.
- A frozen case fails closed when an artifact changes or cross references are invalid.
- The baseline fixture uses only local files at runtime.
- Every artifact required at runtime has a manifest checksum.
- The fixture labels data gaps and source uncertainty instead of hiding them.

## Files added

- `pyproject.toml`
- `backend/src/climate_cascade/domain/models.py`
- `backend/src/climate_cascade/domain/fixtures.py`
- `backend/tests/test_domain_models.py`
- `backend/tests/test_frozen_case.py`
- `data/fixtures/cases/nepal-emsr927-v1/`
- `docs/architecture/frozen-case-format.md`

## Commands and results

```bash
uv sync --all-groups
```

Result: passed. The lock resolved 12 packages and created a local Python 3.13.5 environment with Pydantic 2.13.5 and pytest 9.1.1.

```bash
uv run pytest backend/tests/test_domain_models.py
```

Initial result: failed during collection because `ActionUrgency` was defined in `models.py` but missing from the public `climate_cascade.domain` export. The export was added, then the focused suite was rerun.

```bash
uv run pytest backend/tests/test_domain_models.py -q
```

Result: passed, `7 passed in 0.06s` after adding the unknown-field contract check.

```bash
uv run pytest backend/tests/test_frozen_case.py
```

Result: passed, `3 passed in 0.07s`.

```bash
uv run python -m compileall -q backend/src
uv run pytest
uv lock --check
```

Result: all passed. The final full suite reported `10 passed in 0.07s`; the lockfile check resolved 12 packages without changes.

One final-suite attempt did not start because the command runner used a misspelled workspace path. No project command executed. The identical command was rerun from `/Users/karanahuja/AI_Workload/micro1_hackathon` and passed.

```bash
uv run python -c 'from pathlib import Path; from climate_cascade.domain import load_frozen_case; bundle = load_frozen_case(Path("data/fixtures/cases/nepal-emsr927-v1")); print(f"fixture={bundle.manifest.fixture_id} mode={bundle.manifest.run_mode.value} artifacts={len(bundle.manifest.artifacts)} gold_actions={len(bundle.gold_actions.actions)}")'
```

Result: `fixture=nepal-emsr927-v1 mode=baseline artifacts=3 gold_actions=4`.

## Findings

- Domain contracts reject unknown fields, timezone-free timestamps, invalid estimate ranges, estimates attached to the wrong action, and short reviewer rationales.
- The fixture loader validates file hashes before parsing content, then validates case IDs, hazard types, and gold-action source and constraint references.
- The tamper test proves that a changed input file is rejected.
- The cross-reference test proves that even a checksum-updated file is rejected when it refers to an unknown source.
- The fixture is ready for the direct-prompt baseline contract, but no baseline model run has been implemented or measured yet.

## Evidence source boundary

The CEMS activation response was queried on 2026-08-29 and its raw response SHA-256 is retained in the curated fixture metadata. The full raw response and geospatial products are intentionally deferred to Iteration 1 source snapshotting.

## Documentation updates

- Added `docs/architecture/frozen-case-format.md`.
- Added `docs/execution/README.md` and this entry.
- Updated the product, evaluation plan, architecture decision record, story, improvement changelog, and project skills with fixture and test-evidence references.

## Decision and next step

Keep the domain schema and fixture boundary. Proceed to ADR implementation step 2: implement the direct-prompt baseline and its repeatable evaluation output using this frozen case format.
