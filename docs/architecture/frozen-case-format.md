# Frozen Case Format

Status: Implemented for the baseline fixture format  
Schema version: `1`  
Owner: Domain contracts and evaluation harness

## Purpose

A frozen case is the reproducible input boundary shared by the direct-prompt baseline and every later agent iteration. It makes data drift visible, prevents silent changes to benchmark inputs, and keeps synthetic operational constraints distinct from public source facts.

The first case is [Nepal EMSR927 baseline fixture](../../data/fixtures/cases/nepal-emsr927-v1/README.md). It is a cited curated dossier, not a raw-source snapshot. Iteration 1 adds full source snapshotting and verification.

## Directory layout

```text
data/fixtures/cases/<fixture-id>/
  manifest.json
  incident_dossier.json
  operational_scenario.json
  gold_actions.json
  README.md
```

| File | Purpose |
| --- | --- |
| `manifest.json` | Fixture identity, version, mode, hazard type, and SHA-256 checksums for every runtime input |
| `incident_dossier.json` | Public, cited event and impact facts, evidence status, data gaps, and safety note |
| `operational_scenario.json` | Explicit synthetic or source-backed operating constraints used for scoreable scenarios |
| `gold_actions.json` | Severity-weighted expected protective outcomes and forbidden action patterns |
| `README.md` | Human-readable provenance, use boundary, and fixture caveats |

## Integrity contract

`load_frozen_case()` validates the manifest before returning any data:

1. Every required input is declared in the manifest.
2. Every declared file exists inside the fixture directory.
3. Every SHA-256 digest matches exactly.
4. The dossier, scenario, and gold-action set use the manifest fixture ID.
5. The hazard type matches across manifest and event.
6. Every gold action references existing evidence and constraint IDs.

Any mismatch fails closed with `FrozenCaseIntegrityError`.

## Data-classification rules

- Public cited facts must identify their publisher, HTTPS URL, retrieval time, materialization type, and license note.
- Curated summaries are allowed for the direct-prompt baseline only and must say so in the fixture README.
- Raw upstream snapshots, checksums, and licensing records are mandatory when Iteration 1 source verification is implemented.
- Synthetic constraints must set `origin: "synthetic"` and cannot cite external source IDs.
- Source-backed constraints must identify the source IDs that support them.
- Gold actions are evaluation labels, not operational instructions.
- Missing coverage is represented as a data gap, never as an unaffected area.

## Versioning and change procedure

Do not alter a fixture after it has been used for a recorded baseline or agent result.

1. Create a new directory with a new fixture ID or version.
2. Recalculate every artifact checksum in `manifest.json`.
3. Add or update fixture tests.
4. Rerun baseline and affected agent evaluations on the new fixture set.
5. Record the exact change, command, results, and decision in `docs/solution_improvement/` and `docs/execution/`.
6. Update `docs/evaluation/README.md` if the benchmark definition changes.

## Verification command

```bash
uv run pytest backend/tests/test_frozen_case.py
```

The complete domain-contract suite runs with:

```bash
uv run pytest
```
