# Solution Improvement Changelog

Status: Started before implementation  
Last updated: 2026-08-29

This is the evidence-backed history of how the Climate Cascade Response Agent improves over its baseline. Append one entry for every meaningful experiment, including experiments that are later removed.

Do not backfill successful-looking results. Record the hypothesis before implementation, run the same frozen evaluation cases, and keep failed results.

## Current progression

| Stage | What we tried and why | Evidence | Decision or learning |
| --- | --- | --- | --- |
| Product discovery | Selected post-disaster action planning because a map alone does not tell an emergency manager what to do, where, why, or under whose authority. Defined Nepal `EMSR927` as the pilot and identified public CEMS, WorldPop, OpenStreetMap, HydroRIVERS, GHSL, and USGS inputs. | Source verification and product plan in `docs/product.md`; architecture decisions in `docs/architecture/ADR-0001-iterative-agentic-architecture.md`; no solution metric yet. | Keep the hackathon MVP narrow: verified flood/debris impacts to human-reviewed action records. Use a deterministic orchestrator, two bounded model roles, typed tools, and explicit memory. Preserve a hazard-adapter boundary for post-MVP work without claiming cross-hazard validation. |
| Foundation: domain schemas and frozen case, completed | Added versioned Pydantic models for event, evidence, impact, scenario, gold-action, review, estimate, progress, and manifest contracts. Added checksum-verified Nepal `EMSR927` baseline fixture with cited curated facts, explicit data gaps, and synthetic constraints. | `docs/execution/2026-08-29-domain-schemas-and-frozen-case.md`; final `uv run pytest` reported `10 passed in 0.07s`; `uv lock --check` passed. Initial domain-test collection failed because `ActionUrgency` was not exported, then passed after the public export was fixed. | Keep. The fixture boundary is reproducible and fails closed on tampering or broken references. Baseline model execution and LSAC@5 remain unmeasured. |
| Baseline, planned | One direct prompt receives the same flattened event dossier and required action schema as the final system. It has no tools, retries, memory, verifier, or geospatial calculations. | Not run. | Implement and freeze this before adding the advanced workflow. |
| Baseline, implemented | One OpenAI-compatible structured completion receives the frozen dossier and scenario. It writes draft actions only, has no tools, retries, memory, verifier, human-feedback loop, or life-safety estimator. A deterministic evaluator checks response structure, evidence IDs, policy patterns, and LSAC@5 from explicit human adjudication. | Focused tests: `9 passed`. Local CLI run without `OPENAI_API_KEY` produced a `provider_not_configured` run artifact and `run_failed` evaluation artifact, as designed. No model output or numeric LSAC@5 exists yet. | Keep. The baseline is reproducible and fails closed. Run a credentialed Nepal case, store human adjudication, then materialize closed CEMS benchmark cases before comparing an improved workflow. |
| Iteration 1, planned | Add authoritative source adapters, evidence snapshots, claim agreement, freshness, licensing, and abstention. | Not run. | Test whether evidence precision improves without reducing critical-action coverage. |
| Iteration 2, planned | Add deterministic population, asset, and road-connectivity calculations. | Not run. | Test population error, asset F1, and duplicate-population rate. |
| Iteration 3, planned | Add typed action templates, ranking, ownership, dependencies, and an evidence verifier. | Not run. | Test LSAC@5 and unsupported-action rate. |
| Iteration 4, planned | Add potential-lives-saved ranges, editable assumptions, and approve/edit/reject/request-evidence feedback. | Not run. | Test interval coverage, abstention, safety, and review time. |

## Append-only experiment template

### Iteration `<number>`: `<short name>`

- **Date:**
- **Status:** planned, running, kept, revised, or removed
- **Observed failure or opportunity:**
- **Hypothesis:**
- **Change:**
- **Evaluation cases and version:**
- **Primary metric before:**
- **Primary metric after:**
- **Safety metrics:**
- **Runtime and cost:**
- **Evidence paths:**
- **Decision:** keep, revise, or remove
- **Learning:**
- **Story update made:** yes or no, with path
- **Next experiment:**

## Evidence discipline

- Never replace a historical result without recording a correction.
- Link every metric to machine-readable evaluation output.
- Record exact commands, model names, model versions where available, prompts, dependency versions, runtime, and cost.
- Preserve representative trajectories showing tool responses, retries, verifier feedback, and human checkpoints.
- If an iteration changes the dataset or rubric, rerun the baseline and explain the change.
- Update `docs/story/README.md` after every measured iteration so the submission narrative reflects evidence rather than memory.
