---
name: climate-cascade-response
description: "Plan, build, evaluate, and document the Climate Cascade Response Agent in this workspace, including its verified disaster inputs, post-disaster action dashboard, human approvals, iterative evidence, and Micro1 submission story."
---

# Climate Cascade Response

Use this skill for all product, implementation, evaluation, and submission work on the Climate Cascade Response Agent.

Before substantial work, read the relevant project files:

- [product plan](../../../docs/product.md) for scope, architecture, inputs, outputs, and safety invariants
- [architecture decision record](../../../docs/architecture/ADR-0001-iterative-agentic-architecture.md) before changing agents, orchestration, tools, contracts, APIs, persistence, memory, configuration, or downstream integrations
- [evaluation plan](../../../docs/evaluation/README.md) before changing the baseline, metrics, fixtures, or benchmark
- [improvement changelog](../../../docs/solution_improvement/README.md) before implementing an iteration
- [project story](../../../docs/story/README.md) before changing the dashboard flow, demo, claims, or submission narrative

## Product outcome

Turn a verified post-disaster event into a ranked, evidence-backed action queue for an emergency manager. Show affected population and infrastructure, an uncertainty-aware potential-lives-saved range or `not estimable`, and the evidence behind every action. A qualified human must approve, edit, request evidence, or reject each consequential action.

The Micro1 MVP handles CEMS flood and debris-flow products. The pilot is Nepal `EMSR927`. Beyond the MVP, the product is designed to add separate adapters for earthquakes, tsunamis, tornadoes, and volcanic eruptions.

## Scope discipline

- Label floods and debris flows as the **hackathon MVP**. Use **built and evaluated** only after implementation and stored evaluation evidence exist.
- Label earthquakes, tsunamis, tornadoes, and volcanic eruptions as **beyond-MVP roadmap hazards**.
- Say the architecture is **designed to extend** to those hazards. Never say the product supports or is validated on them until their adapters and evaluations exist.
- Keep the shared lifecycle, normalized action schema, human review, progress feed, and audit contracts hazard-agnostic.
- Put authoritative sources, severity surfaces, secondary-hazard rules, impact calculations, action policies, and estimator policies behind a typed `HazardAdapter`.
- Require a separate benchmark, fair baseline, gold actions, difficult case, domain review, and safety evidence for each added hazard.
- Never reuse flood thresholds, action rankings, fatality-risk intervals, or intervention-effectiveness assumptions for another hazard.
- Report hazard results separately until evidence justifies aggregation.
- Revisit the product name before claiming geological-hazard support because earthquakes and volcanoes are not climate hazards.

## Project invariants

- This is post-disaster decision support, not hazard prediction.
- Never issue public warnings, evacuation orders, dispatches, or infrastructure commands.
- Keep all consequential actions in simulation until a qualified human explicitly approves them.
- Treat current-event sources as mutable. Pin snapshots with URL, retrieval time, checksum, version, and license.
- Preserve uncertainty. For the Nepal event, do not state that the trigger was definitively a glacier collapse or GLOF while authoritative sources say it remains under investigation.
- Use deterministic code for geospatial overlays, routing, population aggregation, scoring, and life-safety arithmetic.
- Never equate exposed population with lives saved.
- Present potential lives saved only as a modelled low-central-high range with visible assumptions and sourced coefficients. Return `not estimable` when support is missing.
- Spatially deduplicate people before aggregating action-level estimates.
- Treat missing data as unknown, not as proof of no impact.
- Every factual claim and output metric must link to stored evidence.
- Keep private data, credentials, and individual-level records out of the project and submission.
- Make every lifecycle stage, tool call, retry, warning, verifier result, and human checkpoint visible in the run trajectory and dashboard progress feed.
- Fail closed when verification, required data, or human approval is missing.

## Agent lifecycle

Use an explicit, resumable state machine:

`RECEIVED -> SOURCE_CHECK -> VERIFIED|BLOCKED -> DATA_SNAPSHOT -> IMPACT_ANALYSIS -> ACTION_DRAFTING -> EVIDENCE_VERIFICATION -> AWAITING_HUMAN_REVIEW -> APPROVED|REVISION_REQUESTED|REJECTED -> EXPORTED`

Start with one coordinator and typed deterministic tools. Add specialized agents only when evaluation demonstrates a failure that separation fixes. Purposeful design matters more than component count.

Bound retries, make operations idempotent, preserve tool responses, and distinguish source conflict, missing data, tool failure, and model uncertainty.

## Iterative build contract

1. Make the direct-prompt baseline runnable first.
2. Freeze the case schema, benchmark version, primary metric, and safety gates.
3. Implement one testable hypothesis at a time.
4. Run the baseline and changed workflow on the same cases.
5. Record every result, including regressions and removed experiments.
6. Link claims to evaluation artifacts, trajectories, screenshots, commands, runtime, and cost.
7. Append the iteration to `docs/solution_improvement/README.md`.
8. Update `docs/story/README.md` after every measured iteration. Revise the claims ledger, demo beats, failure mode, and hot take so the story follows evidence.
9. Preserve representative trajectories as work happens; do not reconstruct them at the end.
10. Keep the reproduction path working from a clean environment.

If an iteration changes data, prompts, tools, model, rubric, or gold labels, document the resource difference and rerun the baseline.

## Major Checkpoint Documentation

A major code checkpoint is a completed planned capability, contract or schema change, API or dashboard behavior change, workflow or safety-policy change, provider compatibility repair, or any change that affects reproducibility. A major evaluation checkpoint is a completed or failed benchmark, human adjudication, or changed metric result.

Before closing either checkpoint, update the applicable records in the same change:

- `docs/execution/YYYY-MM-DD-NN-short-description.md`: every major code and evaluation checkpoint. Record sequence, commands, tests, verification, artifacts, failures, and the next decision. Use the zero-padded sequence in the filename and preserve prior records.
- `docs/solution_improvement/README.md`: every major code and evaluation checkpoint. Update the affected stage with the final finding, evidence paths, decision, and learning. Add a dedicated findings section when a result is the baseline or a key iteration comparison.
- `docs/evaluation/README.md` and the relevant evaluation guide: every major evaluation checkpoint. Record measured or failed status, exact metric values, safety results, resource use, artifact paths, and limits of the claim. Do not update metrics before the artifact exists.
- `docs/story/README.md`: every measured evaluation checkpoint. Update the baseline or iteration narrative, claims ledger, strongest observed failure, and demo language so they remain evidence-bound.
- `README.md`: when setup, commands, artifacts, benchmark status, runtime, cost, or reproducibility guidance changes.
- `docs/product.md` and the ADR: when scope, architecture, agents, tools, data contracts, safety boundaries, or implementation status changes.

Do not leave a final result only in an artifact or a wide changelog table. The final baseline and each retained major iteration must have a concise, easy-to-find finding with direct artifact links.

## Test and execution evidence protocol

Before implementing a deterministic behavior, define its acceptance criteria and focused tests. For agent behavior, define the frozen cases, output contract, safety checks, and evaluation metric before changing prompts, tools, or policies.

For every meaningful implementation step:

1. Add or update focused tests with the code or fixture change.
2. Run the focused tests, then the relevant full suite.
3. Verify the user-visible or artifact behavior when the change has a dashboard, API, export, fixture, or trajectory effect.
4. Record exact setup, test, and verification commands plus pass, fail, retry, runtime, and environment details in a sequenced `docs/execution/YYYY-MM-DD-NN-short-description.md` record.
5. Append the implementation finding and evidence path to `docs/solution_improvement/README.md`.
6. Update the product, evaluation, ADR, and story documents when the result changes their claims or scope.
7. Do not mark a stage complete while required tests fail, fixture integrity is unverified, or documentation omits the finding.

Required minimum checks by change type:

- Domain contract: valid and invalid Pydantic inputs, schema-version behavior, and unknown-field rejection.
- Fixture: checksum, cross-reference, source-versus-synthetic classification, and local-only loading.
- Deterministic tool: golden-input output, edge cases, idempotency, and error classification.
- Workflow: allowed and forbidden state transitions, retry cap, pause and resume behavior, and audit events.
- Agent: structured output validation, tool allowlist, verifier findings, and safety gate results on frozen cases.
- API or dashboard: contract test plus end-to-end user-visible verification.

Treat `docs/execution/` as append-only evidence. The [execution ledger](../../../docs/execution/README.md) is required reading before closing an implementation step.

## Evaluation contract

Primary metric: **Life-Safety Action Coverage at 5**, the severity-weighted fraction of required critical actions covered by the top five proposals.

Required safety gates:

- unsafe autonomous-action rate: `0%`
- unsupported final-action rate: `0%`
- missing evidence references on approved actions: `0`

Also report evidence precision, population error, asset-impact F1, duplicate-population rate, life-safety interval coverage, abstention correctness, human review time, end-to-end completion, runtime, cost, and clean-environment reproduction success.

Use at least ten fixed cases and one challenging case. Report all cases and failures. The open Nepal event is the challenging case and must be evaluated for uncertainty, freshness, incomplete-data handling, and appropriate abstention rather than included in closed-event impact-accuracy aggregates.

## Micro1 judging criteria

Projects are scored out of 100:

- `15` - **Problem and User Value:** solve a meaningful problem for a clearly defined user; explain who experiences the bottleneck and why it matters.
- `30` - **Agent Solution and Engineering:** use agents purposefully and soundly; show which context, tools, memory, verification, skills, or orchestration choices improved the result.
- `20` - **End-to-End Quality:** complete a realistic, self-contained execution and produce a result the intended user could use and sign their name to.
- `15` - **Measured Improvement:** demonstrate gains over a fair baseline and connect every meaningful iteration to evidence in the changelog.
- `15` - **Reproducibility:** let another person run the baseline and solution from a clean environment and reproduce the main result.
- `5` - **Hot Take and Insights:** turn an observed failure mode into a practical lesson for building more reliable agents.

Tie-break order:

1. Agent Solution and Engineering
2. Reproducibility
3. Measured Improvement
4. End-to-End Quality
5. Final panel review of documented evidence

## Micro1 ground rules

1. Tools and components already known to the builder may be used.
2. Clearly identify what existed before the competition and what was added during it.
3. Use every tool and component according to its license and service terms.
4. Keep consequential actions controlled through a sandbox or simulation and require human approval before action.
5. Include a qualified human reviewer in any solution that could significantly affect someone.
6. Choose a legal and ethical use case that treats people and their data responsibly.
7. Use information that may be shared; prefer public, synthetic, or approved anonymous data.
8. Keep credentials and private information outside the submission.
9. Connect every result claim to submitted evidence.
10. Give judges enough access to run the project and reproduce the main result.

## Required submission package

- complete solution code and a clearly labelled improvement changelog
- clean-environment reproduction guide with exact baseline, solution, and evaluation commands, data, expected outputs, versions, runtime, and approximate cost
- solution video of at most five minutes showing the problem, baseline, realistic end-to-end run, final comparison, key iteration, and one removed experiment
- representative trajectories for every agent, including instructions, tool responses, feedback, retries, and human checkpoints

## Documentation discipline

- Keep `docs/product.md` current when product scope, architecture, inputs, outputs, or safety boundaries change.
- Keep the root `README.md` current as the Micro1 entry point. It must state the intended user and bottleneck, MVP scope and safety boundary, exact setup plus baseline and evaluation commands, expected artifacts, required public or synthetic data, and where a user supplies secrets without committing them.
- Keep README claims evidence-bound. Link the evaluation plan, improvement changelog, story, execution ledger, and trajectories; mark unmeasured results as unmeasured rather than using placeholders or zeroes.
- Update the README whenever dependencies, model configuration, fixture paths, CLI commands, benchmark status, runtime, cost, or reproduction expectations change.
- Keep the MVP-versus-beyond-MVP distinction visible in the product plan, evaluation plan, story, dashboard copy, demo, and submission video.
- Append experiments to `docs/solution_improvement/README.md`; never erase inconvenient results.
- Keep metric definitions and benchmark changes in `docs/evaluation/README.md`.
- Update `docs/story/README.md` after every measured iteration, not only before submission.
- Do not claim actual lives saved. Use `potential fatalities averted under stated assumptions` or `not estimable`.
- Record source attribution and licensing for CEMS, WorldPop, OpenStreetMap, HydroRIVERS, NASA, GHSL, USGS, and any later source.
