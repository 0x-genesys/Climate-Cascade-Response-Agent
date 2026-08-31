# Iteration 2 Live Nepal POC Finalization

- **Date and sequence:** 2026-08-31, record 16
- **Scope:** ADR step 7 deterministic CEMS product-statistics impact engine, dashboard/API exposure, live Nepal run, and authorized project-owner adjudication.
- **Acceptance criteria:** Parse one newest finished product per AOI; extract cited population, assets, roads, bridges, and coverage gaps; do not duplicate product versions; expose an immutable impact artifact; preserve draft-only safety; retain a live trajectory and removed experiment.

## Implementation

Added strict `ImpactPackage`, `AoiImpact`, `PopulationImpact`, `AssetImpact`, and `AccessImpact` contracts. The deterministic tool reads the saved CEMS activation snapshot, chooses the newest finished product per AOI by delivery time and version, extracts product statistics, and records unavailable products as gaps. It does not download or infer raw map geometry, run local raster/vector overlays, or manufacture a route graph.

The worker now saves `impact_package` during `IMPACT_ANALYSIS`, emits start and completion SSE events, passes only compact impact facts to the response supervisor, and exposes `GET /v1/runs/{run_id}/impacts`. The dashboard renders the per-AOI source-reported facts and deduplication note before draft actions appear.

## Live runs and policy decision

Four live `EMSR927` model calls were made while testing explicit, generic selection policy. All were draft-only and used CEMS product statistics.

| Configuration | Result | Decision |
| --- | --- | --- |
| v2 initial urgency policy | Drafted all target locations but used time windows too slow for the transferred rubric. | Revise urgency guidance. |
| v3 distinct-AOI policy | Corrected Timure location coverage but did not produce Syapru continuity. | Revise facility instruction. |
| v4 retained | Covered Timure access, Bidur residential triage, and Bharatpur evidence request; missed Syapru continuity. | Retain as the best evidence-bound POC. |
| v5 facility-capacity policy | Forced additional facility continuity drafts, but omitted Timure access and Bharatpur evidence request under the five-action cap. | Remove. Preserve trajectory, do not tune against hidden gold labels. |

The retained run is `run-f7fd675d-6370-4470-ac51-cc1356b7f581`. It used `gpt-5-mini-2025-08-07`, response-supervisor configuration version `4`, `4,012` prompt tokens, and `3,614` completion tokens. Runtime from first worker event to completed draft checks was about `57` seconds. Provider cost was not captured.

## Deterministic impact result

The saved impact package analyzed three finished AOIs and one explicit gap:

- Syapru Besi: `450` affected population, `429` affected residential buildings, `7.6 km` affected roads, `5` bridge features, and affected power-plant construction source statistics.
- Timure: `450` affected population, `289` affected residential buildings, `9.7 km` affected roads, and `1` bridge feature.
- Bidur: `5,000` affected population, `3,029` affected residential buildings, `49.8 km` affected roads, `26` bridge features, and affected facility source statistics.
- Bharatpur: no finished CEMS product with parseable impact statistics; preserved as a data gap.

All values are source-reported CEMS product statistics. They are not independently calculated casualties, a local spatial overlay, or lives-saved estimates.

## Authorized manual review and evaluation

The project owner authorized an AI-assisted review for this POC. The review is recorded as `project-owner-ai-assisted`, not as credentialed emergency-management adjudication.

| Gold action | Decision | Rationale |
| --- | --- | --- |
| Timure access verification | Covered | The cited Timure draft requested immediate human verification of road and bridge access impacts. |
| Bidur residential triage | Covered | The cited Bidur draft requested immediate location-specific residential-impact triage. |
| Syapru Besi critical-services continuity | Not covered | Syapru Besi appeared in access/residential triage only, not an explicit facility-continuity draft within six hours. |
| Bharatpur data gap | Covered | The monitor-only draft preserved the waiting-product gap and requested evidence. |

```bash
uv run climate-cascade-evaluate-agent \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run runs/iteration_2/nepal-emsr927-live-v4.run.json \
  --evidence runs/iteration_2/nepal-emsr927-live-v4.evidence.json \
  --adjudication runs/iteration_2/nepal-emsr927-live-v4.adjudication.json \
  --evaluation-output runs/iteration_2/nepal-emsr927-live-v4.evaluation.json
```

Result: LSAC@5 `13/17` (`76.47%`), `0` unsafe autonomous-action findings, `0` missing evidence references, and `5` valid evidence references.

## Claim boundary and next step

This is a rubric-transfer diagnostic, not a fair improvement claim against the frozen baseline or Iteration 1. The live CEMS data is mutable, prompt and tool resources differ, and the review is project-owner rather than credentialed. The retained evidence proves that deterministic product-level facts improved the specificity of live drafts and exposed an action-budget trade-off. A fair comparison requires a newly frozen product-level case, pre-frozen gold labels and prompt policy, the baseline rerun on that same input, and credentialed review.

## Verification

Focused impact, supervisor, and workflow/API tests passed before live calls. After final documentation updates, `uv run pytest` reported `50 passed` with one existing Starlette TestClient deprecation warning; `node --check dashboard/app.js`, `uv lock --check`, retained JSON parsing with `jq empty`, a deterministic `climate-cascade-evaluate-agent` rerun, and `git diff --check` all passed before commit.
