# Project Story

Status: Narrative scaffold, updated with baseline and Iteration 1 live POC findings
Last updated: 2026-08-31

## Working title

Climate Cascade Response: From Damage Maps to Life-Safety Actions

## Opening

On 26 August 2026, a rapid slope failure involving a glacier in Nepal sent debris and floodwater roughly 100 km downstream. Satellite teams could map the damage, but a response team still had to answer the questions that determine what happens next:

- Which communities and facilities are affected?
- Which settlements may be isolated by damaged bridges and roads?
- What action should happen first?
- How many people could each action protect?
- Which facts are verified, and which remain uncertain?

The Climate Cascade Response Agent is designed for the gap between a disaster map and a field decision.

## Intended user

An emergency operations analyst needs to turn fragmented, evolving evidence into a short queue of defensible actions. The analyst cannot trust a fluent summary that hides uncertainty, duplicates population, or suggests actions without ownership and evidence.

## Baseline story

The baseline copies the available incident summary into one general-purpose structured-model request and asks for reviewable draft recommendations. It has no retrieval, tools, memory, retries, verifier, geospatial calculations, life-safety estimator, or human-feedback loop. The run artifact preserves the full prompt and exact model response; a deterministic evaluator then checks evidence references and policy patterns, while a human records the semantic gold-action coverage required for LSAC@5.

One credentialed baseline run with `gpt-5-mini-2025-08-07` produced five draft actions. Human adjudication measured LSAC@5 at `3/17` (`17.65%`): the model preserved Bharatpur as a pending data gap, but its generic Rasuwa and Trishuli actions did not cover the location-specific Timure access, Bidur residential-triage, or Syapru Besi critical-services requirements. The deterministic evaluator found no unsafe autonomous-action patterns and no missing evidence references. This is a single difficult open-event result, not a claim that the final workflow improves it.

## Product story

The agent follows a visible lifecycle:

1. verify the event and preserve uncertainty
2. snapshot and cite the data
3. calculate population and infrastructure impact deterministically
4. draft a small action queue
5. verify every claim and estimate
6. ask a qualified human to approve, edit, request evidence, or reject
7. export the signed action brief and complete audit trail

The dashboard does not pretend that an estimated affected population equals lives saved. In the current implementation, every action says `not estimable` with a reason because deterministic impact and life-safety calculations are not built yet.

The final architecture deliberately uses only two model roles: a response supervisor drafts actions from verified evidence, and an independent evidence and safety supervisor challenges those drafts. A deterministic Python state machine controls the workflow, while typed tools perform source access, geospatial analysis, routing, estimation, persistence, and export. This keeps the agentic contribution visible and measurable.

## MVP now, multi-hazard platform later

The hackathon MVP is intended to prove the complete workflow for floods and debris flows. It does not claim that the same hazard analysis works for earthquakes, tsunamis, tornadoes, or volcanic eruptions.

Beyond the MVP, the product can retain its verified-event lifecycle, action schema, human review, dashboard, and audit trail while adding a separate typed adapter for each hazard. Each adapter must bring its own authoritative sources, severity surfaces, secondary-hazard logic, action policies, life-safety assumptions, and evaluation suite.

For judges, the story must use precise language:

- "Hackathon MVP for floods and debris flows" before evaluation, then "built and evaluated" only after the evidence exists
- "Designed to extend to earthquakes, tsunamis, tornadoes, and volcanic eruptions"
- Never "works for all disasters" until separate evidence exists

Earthquake is the first proposed post-MVP adapter. It closely matches the product's life-safety workflow while still forcing a genuinely different impact model based on shaking, structural damage, access disruption, and secondary hazards.

## Demo narrative

### Beat 1: The event arrives

Choose the Nepal live CEMS example (`EMSR927`). Show USGS, CEMS, and International Charter verification. Highlight that the exact trigger is still under investigation.

### Beat 2: The agent works in public

Show the live dashboard run feed moving through source retrieval, source verification, source snapshot, constrained response-supervisor drafting, receipt of the stored structured response, and deterministic draft checks. The dashboard exposes these persisted milestones, not token streaming or private model reasoning. Surface the stored warning that `EMSR927` is open and that Bharatpur is waiting for a product. The dashboard reaches `Ready for human review` only when the draft has cited saved evidence and passed deterministic policy checks. A qualified reviewer can persist approve, edit, request-evidence, or reject decisions, and the queue visibly reflects the latest record. Those decisions are audit records only: the product never dispatches or executes an action.

Use the glossary at the bottom of the dashboard if the reviewer needs to distinguish CEMS, USGS, the International Charter, AOIs, evidence snapshots, automatic Run Feedback, human adjudication, or LSAC@5. Each entry explains where it appears in the flow.

### Beat 3: The useful failure is visible

Show the deterministic impact panel: completed CEMS products now provide source-reported roads, bridges, residential buildings, population, and facility facts for Syapru Besi, Timure, and Bidur, while Bharatpur remains visibly unknown. The retained live POC covers Timure access, Bidur residential triage, and Bharatpur evidence handling. It still misses Syapru Besi facility continuity, which is the honest next failure rather than a hidden one.

### Beat 4: A human remains accountable

Request more evidence for one action, edit an assumption, approve another action, and reject an unsupported action. Show that no action executes automatically.

### Beat 5: Prove improvement

Compare the direct-prompt baseline with the final workflow on the same cases. Show Life-Safety Action Coverage at 5, unsafe actions, evidence precision, population error, review time, runtime, and cost.

### Beat 6: Share the learning

Show the most valuable retained change and one experiment that was removed. Clearly separate the validated flood MVP from the multi-hazard roadmap, then end with the insight supported by the evaluation.

## Current candidate insight

> Product availability tells you where to look. Deterministic product facts are what let a response agent name the right human-reviewed action - but a five-action budget still needs an explicit, testable selection policy.

This is a candidate, not the final hot take. Replace or revise it when a measured failure reveals a stronger practical lesson.

## Claims ledger

| Story claim | Current evidence | Status |
| --- | --- | --- |
| The Nepal event travelled about 100 km downstream | USGS event page | Verified but preliminary |
| The exact initiating mechanism remains uncertain | International Charter; USGS describes a likely glacial collapse but marks its findings preliminary | Verified source disagreement |
| CEMS reported 5,300 affected people and 3,207 affected buildings in its current activation summary | Live `EMSR927` API response observed 2026-08-29 | Dynamic until snapshot is committed |
| The agent improves critical-action coverage | No evaluation yet | Unproven |
| The agent reduces human review time | No evaluation yet | Unproven |
| The agent can estimate potential lives saved responsibly | Model and calibration not implemented | Unproven |
| The shared workflow can support additional hazard adapters | Architecture contract in `docs/product.md`; no additional adapter implemented | Designed, not validated |
| The baseline input boundary is reproducible and tamper-evident | `docs/execution/2026-08-29-01-domain-schemas-and-frozen-case.md`; checksum and cross-reference tests | Verified foundation; one difficult-case model run is now recorded |
| The single-call baseline records exact output and produces a human-adjudicated score without retrying or fabricating a result | `runs/baseline/nepal-emsr927-v1.run.json`; `runs/baseline/nepal-emsr927-v1.adjudication.json`; `runs/baseline/nepal-emsr927-v1.evaluation.json` | Verified on one Nepal challenging-case run; closed-event aggregate remains unmeasured |
| The Iteration 1 workflow preserves live CEMS AOI freshness, uncertainty, and evidence references | `runs/iteration_1/nepal-emsr927-live-poc.evidence.json`; `docs/execution/2026-08-31-15-iteration-1-live-poc-finalization.md` | Verified on one live Nepal POC: automatic checks found `0` unsafe patterns, `0` missing references, and `4` valid references. |
| Live product-status metadata alone does not improve location-specific action coverage | `runs/iteration_1/nepal-emsr927-live-poc.adjudication.json`; `runs/iteration_1/nepal-emsr927-live-poc.evaluation.json`; `docs/evaluation/agent.md` | Qualified finding, not a benchmark: project-owner rubric transfer scored `3/17`, covering Bharatpur but not Timure, Bidur, or Syapru Besi. Snapshot mismatch and reviewer role make this non-comparable with the frozen baseline. |
| Deterministic CEMS product statistics improve location-specific draft coverage | `runs/iteration_2/nepal-emsr927-live-v4.impacts.json`; `runs/iteration_2/nepal-emsr927-live-v4.evaluation.json`; `docs/execution/2026-08-31-16-iteration-2-live-poc-finalization.md` | Qualified live POC, not benchmark: project-owner rubric transfer scored `13/17`, covering Timure, Bidur, and Bharatpur. Syapru continuity remained missed. |
| Over-constraining prompt policy can reduce coverage under a five-action budget | `runs/iteration_2/removed/nepal-emsr927-live-v5-overcoverage.run.json` | Observed removed experiment: forcing facility drafts for all affected AOIs displaced Timure access and Bharatpur data handling. |

## Iteration update protocol

After every measured iteration:

1. Add the experiment and evidence to `docs/solution_improvement/README.md`.
2. Update the baseline or product story with observed behavior.
3. Update the claims ledger, marking claims verified, disproven, qualified, or still unproven.
4. Add the strongest new failure mode.
5. Update the demo beat if the user-visible workflow changed.
6. Revise the candidate hot take only when evidence supports it.
7. Preserve one trajectory segment that makes the change understandable.

Never claim lives were saved. Say that an action has a modelled potential to reduce fatalities under stated assumptions.
