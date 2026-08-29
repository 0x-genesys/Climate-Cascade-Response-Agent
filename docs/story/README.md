# Project Story

Status: Narrative scaffold, to be updated after every measured iteration  
Last updated: 2026-08-29

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

The baseline copies the available incident summary into a general-purpose model and asks for recommendations. It can write plausible prose, but it cannot verify changing sources, calculate geospatial exposure, detect route isolation, deduplicate affected populations, or prove why an action belongs in the top five.

Baseline results have not yet been measured. Replace this paragraph with observed strengths and failures after the baseline run.

## Product story

The agent follows a visible lifecycle:

1. verify the event and preserve uncertainty
2. snapshot and cite the data
3. calculate population and infrastructure impact deterministically
4. draft a small action queue
5. verify every claim and estimate
6. ask a qualified human to approve, edit, request evidence, or reject
7. export the signed action brief and complete audit trail

The dashboard does not pretend that an estimated affected population equals lives saved. Each action displays a modelled low-central-high range or says `not estimable`, along with all assumptions.

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

Load the pinned `EMSR927` Nepal fixture. Show USGS, CEMS, and International Charter verification. Highlight that the exact trigger is still under investigation.

### Beat 2: The agent works in public

Show the run feed moving through source verification, data snapshot, deterministic impact analysis, response-supervisor drafting, and independent evidence verification. Surface one warning about the incomplete Bharatpur AOI.

### Beat 3: Damage becomes an action

Open an affected bridge or residential cluster on the map. Show the connected population, affected infrastructure, proposed owner, urgency, evidence, dependencies, and life-safety estimate or abstention.

### Beat 4: A human remains accountable

Request more evidence for one action, edit an assumption, approve another action, and reject an unsupported action. Show that no action executes automatically.

### Beat 5: Prove improvement

Compare the direct-prompt baseline with the final workflow on the same cases. Show Life-Safety Action Coverage at 5, unsafe actions, evidence precision, population error, review time, runtime, and cost.

### Beat 6: Share the learning

Show the most valuable retained change and one experiment that was removed. Clearly separate the validated flood MVP from the multi-hazard roadmap, then end with the insight supported by the evaluation.

## Current candidate insight

> Disaster maps describe damage. Lives are protected when verified evidence becomes an owned, time-bound action with assumptions and uncertainty visible.

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
| The baseline input boundary is reproducible and tamper-evident | `docs/execution/2026-08-29-domain-schemas-and-frozen-case.md`; checksum and cross-reference tests | Verified foundation; no baseline model result yet |

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
