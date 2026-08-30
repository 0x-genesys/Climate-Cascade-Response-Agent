# Climate Cascade Response Agent

Status: Product plan, pre-implementation  
Last updated: 2026-08-29  
Pilot event: 2026 Nepal debris avalanche and flash flood, Copernicus activation `EMSR927`

## Product decision

Build a post-disaster decision-support agent that turns a verified hazard event into a prioritized, evidence-backed action queue for an emergency manager.

The product does not predict disasters, issue public warnings, order evacuations, or execute field actions. It identifies where people and critical infrastructure may be affected, proposes concrete response actions, estimates the potential life-safety benefit as an explicit range, and waits for a qualified human to approve, edit, or reject every action.

The narrow first version handles flood and debris-flow impacts represented by Copernicus Emergency Management Service (CEMS) mapping products. The first demonstration uses the August 2026 Nepal event.

## Scope at a glance

| Horizon | Product promise | Evidence status |
| --- | --- | --- |
| Hackathon MVP | Flood and debris-flow response from verified CEMS products, population and infrastructure overlays, ranked actions, life-safety ranges or abstention, and qualified human review | Committed Micro1 scope; implementation and evaluation are planned |
| Beyond the MVP | Extend the same post-disaster decision workflow to earthquakes, tsunamis, tornadoes, and volcanic eruptions through hazard-specific adapters | Product roadmap only; not implemented or validated by the hackathon |
| Outside the product | Predict hazards, issue public warnings, order evacuations, dispatch responders, control infrastructure, or replace incident command | Intentionally prohibited |

### Why the hackathon MVP is flood-first

Flood and debris-flow products provide a coherent vertical slice with observed-event geometry, population exposure, infrastructure damage, and access disruption. This lets the team prove one complete lifecycle and compare it fairly with a baseline. Adding several hazards before that evidence exists would weaken the evaluation because each hazard needs different severity models, action policies, datasets, and life-safety assumptions.

The architecture is designed for additional hazards, but the submission must say **designed to extend**, not **validated across hazards**.

## Why this problem is worth solving

### Intended user

The primary user is an emergency operations analyst or incident commander working after a disaster has been verified. Supporting users include mapping teams, humanitarian logistics coordinators, public works officials, and health-service coordinators.

### Bottleneck

Useful evidence arrives in different formats and at different times:

- an official event page describes what is known and what remains uncertain
- satellite products describe observed damage or flood extent
- population rasters estimate where people live
- road and bridge data reveal access failures
- facility data identify hospitals, shelters, power plants, and water infrastructure
- situation reports describe operational constraints

The user must combine these sources quickly, avoid double-counting people, distinguish verified facts from preliminary claims, and turn analysis into actions with owners and deadlines. A map alone does not complete that workflow.

### Product promise

Within one reproducible run, the product will produce:

1. a verified incident evidence brief
2. an impact map with population and infrastructure overlays
3. a ranked queue of concrete, human-reviewable actions
4. an uncertainty-aware potential-lives-saved range for each action when it is defensible
5. an audit trail showing sources, calculations, agent decisions, retries, and human feedback

## Verified pilot event

The pilot is grounded in three authoritative sources. The mechanism is intentionally recorded as uncertain because the sources do not yet support a stronger claim.

| Source | What it verifies | Important limitation |
| --- | --- | --- |
| [USGS event page](https://www.usgs.gov/programs/landslide-hazards/science/2026-nepal-debris-avalanche-and-flash-flood) | On 26 August 2026, a debris flow and flood likely triggered by a glacial collapse travelled about 100 km along downstream rivers. USGS is mapping the event with satellite imagery. | The page explicitly labels its findings preliminary or provisional and subject to revision. |
| [Copernicus EMS activation EMSR927](https://mapping.emergency.copernicus.eu/activations/EMSR927/) and [public activation API](https://mapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?code=EMSR927) | Official rapid-mapping activation for flood extent and damage assessment, including AOIs, product downloads, affected population, buildings, roads, bridges, and facilities. | The activation remains open. AOIs and statistics can change as new products arrive. |
| [International Charter activation 1052](https://disasterscharter.org/activations/flood-in-nepal-activation-1052-) | Confirms the event, records UNITAR acting on behalf of the UN OCHA regional office as requestor, and exposes satellite-derived impact products. | It says that the precise cause of the sudden water surge remains under investigation. |

### Data snapshot for the demo

The product will pin a dated copy of the CEMS API response and downloaded vector products. As observed on 2026-08-29, the activation reported completed grading products for Syapru Besi, Timure, and Bidur, while Bharatpur was still awaiting delivery.

The CEMS summary reported:

- estimated affected population: `5,300`
- identified affected buildings: `3,207`
- affected roads: `46 km`
- affected bridge or elevated-highway features in the three completed AOIs: `26`

These values are source-reported estimates, not independently confirmed casualties. The product must display their source, retrieval time, and data status.

Casualty figures will not be used in the MVP because they are changing rapidly and do not determine the geospatial or workflow evaluation.

## Streamlined inputs

### Primary path

The user supplies only:

1. a CEMS activation code or URL, such as `EMSR927`
2. an optional second authoritative event URL
3. optional operational constraints, such as unavailable routes or response-team capacity

The system discovers the AOIs and available products, snapshots them, obtains population and infrastructure layers, and shows the proposed data package before analysis begins.

### Demo path

The dashboard includes a single `Load Nepal EMSR927 fixture` action. This loads pinned local copies rather than depending on live services during judging.

The initial baseline fixture follows the [frozen case format](architecture/frozen-case-format.md): a checksum-verified cited dossier plus explicit synthetic constraints. Full upstream source snapshots are added in Iteration 1.

### Advanced import path

For events without CEMS coverage, an analyst may upload:

- a GeoJSON or GeoPackage hazard extent
- a GeoTIFF population raster
- an infrastructure GeoJSON or CSV
- a signed or otherwise approved situation report

The advanced path is not required for the first complete end-to-end version.

## Tangible outputs

### Incident evidence brief

A concise, cited statement of:

- what happened
- where and when it happened
- what is verified
- what is preliminary or conflicting
- which datasets were used
- when each dataset was retrieved
- which areas were not analyzed

### Impact map

The map shows:

- observed flood or debris extent
- affected and potentially isolated population
- affected buildings and critical facilities
- blocked or affected roads and bridges
- candidate action locations
- data gaps and unanalysed areas

### Action queue

Every action is a durable, exportable record with:

| Field | Meaning |
| --- | --- |
| Action | A concrete verb-first response step, not a general recommendation |
| Location | Polygon, point, route, or named AOI |
| Trigger | Evidence or condition that makes the action relevant |
| Owner | Human role expected to decide or execute |
| Urgency | Immediate, under 6 hours, under 24 hours, or monitor |
| Population basis | Exposed population connected to the action, with source and deduplication method |
| Disaster impact | Affected people, buildings, roads, bridges, and facilities relevant to the action |
| Potential lives saved | Modelled low-central-high range, or `not estimable` |
| Assumptions | Hazard severity, timing, intervention effectiveness, and overlap assumptions |
| Evidence | Source claims, map layers, calculations, and timestamps |
| Confidence | High, medium, low, or blocked |
| Dependencies | Access, personnel, equipment, weather, or preceding actions |
| Human decision | Approve, edit, request evidence, reject, with reviewer rationale |

Example action classes for the Nepal fixture include verifying access to bridge-isolated settlements, prioritizing search-and-rescue verification around affected residential clusters, checking water and medical supply continuity, inspecting damaged hydropower or dam assets, and monitoring downstream areas for secondary hazards. These are candidates for review, not operational instructions.

### Exports

- incident brief as Markdown and printable PDF
- action queue as JSON and CSV
- map layers as GeoJSON
- complete run audit as JSON Lines
- representative agent trajectory with tool responses and human checkpoints

## Potential-lives-saved model

The product must not turn `people exposed` into `lives saved`. Potential lives saved is a counterfactual estimate:

```text
potential lives saved
  = uniquely exposed population reached by the action
  x no-action fatality risk
  x intervention risk-reduction effectiveness
  x probability the action is completed in time
```

The calculator is deterministic. It returns low, central, and high values from sourced parameter intervals. The language model never performs or silently alters this arithmetic.

Rules:

- Never display a single precise number without a range.
- Never sum overlapping action estimates until the target populations have been spatially deduplicated.
- Show `not estimable` when fatality-risk or effectiveness evidence is missing.
- Separate `people exposed`, `people reachable`, `people protected`, and `potential fatalities averted`.
- Label all values as modelled estimates, never as actual lives saved.
- Require the reviewer to inspect assumptions before approval.
- Use synthetic intervention coefficients in the hackathon evaluation unless a citable, hazard-specific model is available.

For example, a synthetic benchmark may specify 450 uniquely exposed people, a no-action fatality-risk interval, and an intervention-effectiveness interval. The dashboard may calculate a range for that fixture, but it must not reuse those coefficients for the real Nepal event.

## Agent lifecycle

The architecture uses one coordinator with typed tools and an independent verification step. Additional agents are added only when evaluation shows that separation improves reliability.

```text
RECEIVED
  -> SOURCE_CHECK
  -> VERIFIED or BLOCKED
  -> DATA_SNAPSHOT
  -> IMPACT_ANALYSIS
  -> ACTION_DRAFTING
  -> EVIDENCE_VERIFICATION
  -> AWAITING_HUMAN_REVIEW
  -> APPROVED, REVISION_REQUESTED, or REJECTED
  -> EXPORTED
```

### Lifecycle responsibilities

1. **Receive:** Parse the activation code and validate the input shape.
2. **Verify:** Check authoritative-source identity, retrieval time, event agreement, and unresolved conflicts.
3. **Snapshot:** Download only required data, calculate hashes, and store licensing metadata.
4. **Analyze:** Run deterministic geospatial overlays, population aggregation, asset intersection, and route connectivity checks.
5. **Draft:** Convert verified impacts into action candidates using a constrained action schema and policy templates.
6. **Estimate:** Run the deterministic life-safety impact calculator where parameters are available.
7. **Verify:** Reject unsupported claims, duplicate populations, missing sources, impossible routes, and unsafe autonomous actions.
8. **Review:** Present actions to a qualified human with evidence and editable assumptions.
9. **Learn:** Record approve, edit, reject, and request-evidence feedback for the current run and future evaluation. Do not silently turn feedback into global policy.
10. **Export:** Produce the incident brief, action queue, map layers, and trajectory.

### Agent design fundamentals

- Use the least agency required for the task.
- Keep consequential actions behind explicit human approval.
- Keep geospatial calculations and scoring deterministic.
- Use typed inputs and outputs at every tool boundary.
- Preserve source provenance through every transformation.
- Fail closed when required data or evidence is absent.
- Make retries bounded, visible, and idempotent.
- Distinguish tool failure, missing data, source conflict, and model uncertainty.
- Persist a run state so work can resume without duplicating downloads or actions.
- Expose progress events instead of hiding long-running work behind a spinner.
- Keep prompts, tool inputs, tool outputs, and reviewer feedback in the trajectory, excluding secrets.

## Proposed technical architecture

The detailed implementation decisions, iteration flows, contracts, persistence model, memory boundaries, agent configuration, and alternatives are recorded in [ADR-0001: Iterative Agentic Architecture](architecture/ADR-0001-iterative-agentic-architecture.md).

### Dashboard

- React and TypeScript
- MapLibre GL JS for the interactive map
- server-sent events for live agent-run feedback
- accessible table and map alternatives so important actions are not map-only

### API and workflow

- Python and FastAPI
- Pydantic models for event, evidence, impact, action, estimate, and review records
- explicit finite-state workflow controlled by application code
- one tool-calling coordinator model behind a provider adapter
- separate deterministic verifier before human review

### Geospatial tools

- GeoPandas, Shapely, Rasterio, and PyProj for overlays and population calculations
- NetworkX for a bounded road-access graph in the AOI
- GeoJSON, GeoPackage, and Cloud Optimized GeoTIFF as interchange formats

### Persistence

- SQLite for runs, evidence, actions, reviews, and progress events
- content-addressed local files for source snapshots
- JSON Lines for exportable trajectories

This local-first architecture avoids requiring PostGIS or a cloud account during judging.

## Multi-hazard architecture beyond the MVP

The response workflow remains stable across hazards: verify the event, snapshot evidence, calculate impact, draft actions, verify claims, obtain human decisions, and export the audit. Hazard science does not remain the same. Each supported hazard must implement a typed `HazardAdapter` rather than adding conditionals to the coordinator.

```text
HazardAdapter
  -> event evidence and source policy
  -> observed or modelled severity surfaces
  -> affected-population and asset rules
  -> access and service-disruption signals
  -> secondary-hazard signals
  -> action-policy catalogue
  -> life-safety estimator policy or mandatory abstention
```

The normalized outputs feed the existing impact, action, verification, review, dashboard, and export contracts. Every adapter must carry units, timestamps, provenance, uncertainty, geographic coverage, and data-completeness warnings.

### Beyond-MVP hazard roadmap

| Hazard | Hazard-specific evidence and analysis | Example human-reviewed outputs | Candidate authoritative sources |
| --- | --- | --- | --- |
| Earthquake | Shaking intensity, exposed structures, likely access failures, and secondary fire, landslide, or liquefaction indicators | Prioritize structural reconnaissance, verify hospital access, identify isolated population clusters, and stage search-and-rescue review | [USGS ShakeMap](https://earthquake.usgs.gov/data/shakemap/) and event products |
| Tsunami | Observed or modelled inundation, water-level observations, coastal access, shelter capacity, and port or hospital disruption | Verify inundated communities, inspect shelter and medical access, prioritize isolated coastal areas, and monitor cascading infrastructure failures | [U.S. Tsunami Warning System data](https://www.tsunami.gov/) plus post-event satellite mapping |
| Tornado | Official damage paths, surveyed damage points, structural severity, utility disruption, and blocked-road evidence | Prioritize welfare checks and medical access, inspect critical facilities, clear access routes, and identify shelter gaps | [NOAA/NWS Damage Assessment Toolkit guidance](https://training.weather.gov/wdtd/courses/damage-surveying/) and official damage surveys |
| Volcanic eruption | Verified activity status, hazard zones, ashfall, lava, pyroclastic-flow or lahar exposure, and downwind infrastructure effects | Review access restrictions, protect water and health services, prioritize roof or ash-load inspections, and identify lahar-isolated communities | [USGS Volcano Hazards Program](https://www.usgs.gov/volcanoes/) alerts, APIs, and hazard assessments |

Roadmap entries are source candidates, not committed integrations. Before adding a hazard, the team must verify access, licensing, geographic coverage, update behavior, and reproducibility.

### Extension rules

- Add one hazard only after the flood MVP meets its acceptance and safety gates.
- Create a separate pinned benchmark, fair baseline, gold actions, and difficult case for each hazard.
- Never reuse flood severity thresholds, fatality-risk intervals, intervention-effectiveness assumptions, or action rankings for another hazard.
- Keep the shared action and review schema only where the semantics remain valid.
- Report cross-hazard results separately until evidence supports an aggregate.
- Revisit the product name before claiming support for geological hazards because earthquakes and volcanoes are not climate hazards.

## Dashboard experience

### Incident header

- event name, status, location, time, and verification badge
- authoritative sources with retrieval timestamps
- unresolved mechanism or data conflicts
- data freshness and snapshot hash

### Impact summary

- exposed population
- affected population reported by the source
- affected buildings, roads, bridges, and facilities
- isolated population estimate
- unanalysed areas and missing layers

### Live agent run feed

The frontend receives structured events:

```text
run_started
source_check_started
source_verified
source_conflict_found
dataset_download_started
dataset_snapshotted
impact_analysis_completed
action_candidate_created
verification_failed
human_review_requested
run_completed
run_failed
```

Every event includes a timestamp, stage, status, plain-language message, evidence references, and retry count. The UI shows active work, completed steps, warnings, and why the system stopped.

### Action review workspace

- ranked action cards synchronized with map locations
- evidence drawer containing source excerpts and calculations
- editable assumptions for the impact estimate
- `Approve`, `Edit`, `Request evidence`, and `Reject` controls
- required reviewer rationale
- visible recalculation when assumptions change

### Comparison and evidence tab

- baseline and agent outputs on the same case
- primary and safety metrics
- iteration changelog
- representative trajectory
- exact reproduction commands once implementation starts

## Public sample data

| Dataset | Planned use | Access and reproducibility | License or constraint |
| --- | --- | --- | --- |
| [CEMS Rapid Mapping API documentation](https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/) | Discover activations, AOIs, product status, statistics, and download paths | Public JSON API; pin response and product archives | Free, full, open access with required citation; products are provided as-is |
| [EMSR927 activation API](https://mapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?code=EMSR927) | Pilot event metadata and current impact statistics | Dynamic endpoint; snapshot with retrieval time and SHA-256 | Cite `Copernicus Emergency Management Service (© 2026 European Union), EMSR927` |
| [EMSR927 product packages](https://mapping.emergency.copernicus.eu/activations/EMSR927/) | Observed-event, building, facility, transportation, and grading layers | Product ZIP URLs are exposed by the activation API | Respect source metadata and any third-party imagery restrictions inside each package |
| [WorldPop Nepal 2025, 100 m](https://hub.worldpop.org/geodata/summary?id=55698) | Population per grid cell for exposure estimates | Approximately 30 MB GeoTIFF; clip and pin the AOI subset | CC BY 4.0; beta product, so show uncertainty and version |
| [OpenStreetMap Nepal extract](https://download.geofabrik.de/asia/nepal.html) | Roads, bridges, settlements, hospitals, clinics, shelters, and utility features | Prefer a pinned AOI extract rather than the full country file | ODbL; display attribution and preserve share-alike obligations for derived databases |
| [HydroRIVERS](https://www.hydrosheds.org/products/hydrorivers) | River-network context and downstream connectivity | Clip the Asia layer to the event corridor | Free for scientific and commercial use under HydroSHEDS terms; citation required |
| [NASA SRTM](https://www.earthdata.nasa.gov/centers/lp-daac) | Elevation and slope context where needed | 30 m data may require Earthdata access; therefore optional for the first reproducible path | NASA/LP DAAC terms and product citation apply |
| [GHSL](https://human-settlement.emergency.copernicus.eu/GHSLWeGenerateData.php) | Independent population and settlement sensitivity check | Open download; use a clipped, pinned subset | CC BY 4.0 |
| [USGS pilot-event map](https://www.usgs.gov/media/images/2026-nepal-debris-avalanche-and-flash-flood-map) | Independent event verification and visual context | Publicly accessible map | Public domain |

The repository will eventually include only small pinned fixtures and download scripts. Large or restricted imagery will not be committed.

## Baseline and iterative architecture

The same case schema and evaluation harness will be used at every stage.

### Baseline: direct incident-to-action prompt

Provide a general-purpose model with one flattened event dossier containing the same source summaries and CEMS impact table available to the final workflow. Ask it once to return the required action schema.

The baseline has:

- no live retrieval
- no source-verification tool
- no geospatial calculations
- no memory
- no retries
- no independent verifier

This is intentionally simple but realistic. It represents an analyst copying available information into a general-purpose assistant.

Implementation status: the single-call structured baseline, deterministic evaluator, SQLite persistence, content-addressed artifact store, FastAPI run control plane, ordered SSE progress stream, leased worker workflow, local `uv run climate-cascade-local` setup/startup path, CEMS source adapter, versioned source-evidence package, and source-intake dashboard are implemented. The recorded Nepal baseline result is LSAC@5 `3/17` (`17.65%`) after human adjudication. Iteration 1 completes source verification and deliberately blocks before impact analysis, action drafting, life-safety estimation, or human action review. It is not a final-agent result or an LSAC improvement. See [baseline evaluation](evaluation/baseline.md), [Iteration 1 execution record](execution/2026-08-30-06-iteration-1-source-intake-dashboard.md), and [source-intake artifacts](../runs/iteration_1/).

### Iteration 1: verified event intake

Implemented for CEMS Rapid Mapping activations: a typed adapter retrieves and canonicalizes the public activation response, records a SHA-256 snapshot, publisher, URL, retrieval time, and license note, then produces typed claims, findings, AOI product status, and data gaps. The workflow stops after source intake until Iteration 2 deterministic impact analysis exists. The local dashboard exposes run progress through the persisted SSE feed and renders the stored evidence package for a pinned fixture or live activation.

Observed source-intake result: live `EMSR927` was correctly marked `preliminary` because the activation is open and two products were waiting for data. Historical flood activations `EMSR756` and `EMSR851` were marked `supported` with no source-level data gaps. This validates the source-verification contract and abstention surface, not evidence precision or action coverage. See [Iteration 1 evidence](../runs/iteration_1/).

### Iteration 2: deterministic impact engine

Add hazard-to-population overlays, asset intersection, spatial deduplication, and road/bridge connectivity analysis.

Hypothesis: deterministic tools will improve population and infrastructure accuracy while reducing arithmetic errors and double counting.

### Iteration 3: constrained action planner

Add typed action templates, action ranking, owner and dependency assignment, and a verifier that checks each action against impact evidence.

Hypothesis: structured planning will improve critical-action coverage and end-to-end usefulness without increasing unsafe recommendations.

### Iteration 4: impact ranges and human feedback

Add the deterministic potential-lives-saved model, assumption editing, approve/edit/reject/request-evidence controls, and feedback capture.

Hypothesis: transparent ranges and human checkpoints will improve decision confidence and reduce false precision.

### Final integration

Add dashboard polish, run progress, exports, clean-environment setup, pinned fixtures, complete trajectories, and the final baseline comparison.

Every iteration must update [the improvement changelog](solution_improvement/README.md), [the project story](story/README.md), and [the evaluation evidence](evaluation/README.md).

## Evaluation strategy

The primary metric is **Life-Safety Action Coverage at 5**, the severity-weighted fraction of required critical actions present in the top five recommendations.

Safety and quality metrics prevent a superficially high score:

- unsafe autonomous-action rate
- unsupported-action rate
- evidence precision
- population-impact error
- duplicate-population rate
- potential-lives-saved interval coverage on synthetic fixtures
- human review time
- runtime and model cost
- clean-environment reproduction success

The benchmark uses ten closed CEMS AOIs with real hazard and impact products plus one deliberately difficult, still-evolving Nepal case. Operational scenario manifests add known road, bridge, facility, and response constraints so expected actions remain objectively scoreable.

See [docs/evaluation/README.md](evaluation/README.md) for definitions, targets, cases, and rubric mapping.

## Scope boundaries

### Included in the MVP

- verified ingestion of a CEMS flood activation
- pinned public datasets
- population and infrastructure impact calculation
- route-isolation checks within bounded AOIs
- evidence-backed action queue
- modelled life-safety range with explicit abstention
- live progress feed
- human review and export
- baseline and repeatable evaluation

### Beyond the MVP

- earthquake response through a USGS-backed hazard adapter
- tsunami response through inundation, water-level, and coastal-access adapters
- tornado response through official damage-path and survey adapters
- volcanic-eruption response through activity, hazard-zone, ashfall, lava, and lahar adapters
- separate hazard-specific benchmarks, estimators, action policies, and safety evidence

These items are architectural commitments and roadmap candidates. They are not hackathon deliverables, and flood evaluation results must not be presented as evidence that they already work.

### Explicitly excluded

- autonomous public alerts or evacuation orders
- prediction of glacier collapse or flood timing
- dispatching responders or controlling infrastructure
- individual-level tracking
- use of private or personally identifiable data
- casualty estimation from social media
- unsupported medical, engineering, or hydrological advice
- global real-time coverage in the first version

## Product acceptance criteria

The first complete version is ready for evaluation when:

1. A judge can select a pinned activation and complete a run from a clean environment.
2. The dashboard shows every lifecycle stage and any retry or failure.
3. Every impact value links to its input layer and deterministic calculation.
4. Every action has a location, owner, urgency, evidence, confidence, and human decision state.
5. Every life-safety estimate is a range with visible assumptions, or says `not estimable`.
6. No consequential action can leave `AWAITING_HUMAN_REVIEW` without explicit approval.
7. The baseline and final workflow run on the same benchmark cases.
8. The evaluation reports all cases, including failures and the challenging case.
9. A clean run exports the incident brief, action queue, map layers, and trajectory.
10. The changelog and story identify the most valuable retained change and at least one removed experiment.

## Main risks

| Risk | Response |
| --- | --- |
| Current-event data changes during development | Pin source snapshots and separate the live demo from the fixed benchmark |
| False precision in lives-saved estimates | Use intervals, expose assumptions, deduplicate populations, and abstain when coefficients are unsupported |
| Impressive map but weak user workflow | Treat approved action records and exports as the product, with the map as supporting evidence |
| Excessive multi-agent complexity | Start with one coordinator and deterministic tools; add specialization only after measured failure |
| Sparse or inconsistent infrastructure data | Show completeness warnings, compare independent layers where practical, and never interpret missing data as absence |
| Unsafe operational interpretation | Keep the product in simulation, require qualified review, and label outputs as decision support |
| Live APIs fail during judging | Use small pinned fixtures and provide optional refresh scripts |
| Benchmark actions become subjective | Use explicit scenario manifests, official response protocols, and severity-weighted gold actions |

## Candidate project insight

The likely hot take is:

> Disaster maps describe damage. Lives are protected when verified evidence becomes an owned, time-bound action with assumptions and uncertainty visible.

This remains a hypothesis until the iteration evidence shows which design change actually improves the outcome.
