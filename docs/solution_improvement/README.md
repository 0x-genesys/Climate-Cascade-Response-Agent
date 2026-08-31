# Solution Improvement Changelog

Status: Started before implementation  
Last updated: 2026-08-31

This is the evidence-backed history of how the Climate Cascade Response Agent improves over its baseline. Append one entry for every meaningful experiment, including experiments that are later removed.

Do not backfill successful-looking results. Record the hypothesis before implementation, run the same frozen evaluation cases, and keep failed results.

## Current progression

| Stage | What we tried and why | Evidence | Decision or learning |
| --- | --- | --- | --- |
| Product discovery | Selected post-disaster action planning because a map alone does not tell an emergency manager what to do, where, why, or under whose authority. Defined Nepal `EMSR927` as the pilot and identified public CEMS, WorldPop, OpenStreetMap, HydroRIVERS, GHSL, and USGS inputs. | Source verification and product plan in `docs/product.md`; architecture decisions in `docs/architecture/ADR-0001-iterative-agentic-architecture.md`; no solution metric yet. | Keep the hackathon MVP narrow: verified flood/debris impacts to human-reviewed action records. Use a deterministic orchestrator, two bounded model roles, typed tools, and explicit memory. Preserve a hazard-adapter boundary for post-MVP work without claiming cross-hazard validation. |
| Foundation: domain schemas and frozen case, completed | Added versioned Pydantic models for event, evidence, impact, scenario, gold-action, review, estimate, progress, and manifest contracts. Added checksum-verified Nepal `EMSR927` baseline fixture with cited curated facts, explicit data gaps, and synthetic constraints. | `docs/execution/2026-08-29-01-domain-schemas-and-frozen-case.md`; final `uv run pytest` reported `10 passed in 0.07s`; `uv lock --check` passed. Initial domain-test collection failed because `ActionUrgency` was not exported, then passed after the public export was fixed. | Keep. The fixture boundary is reproducible and fails closed on tampering or broken references. Baseline model execution and LSAC@5 remain unmeasured. |
| Baseline, planned | One direct prompt receives the same flattened event dossier and required action schema as the final system. It has no tools, retries, memory, verifier, or geospatial calculations. | Not run. | Implement and freeze this before adding the advanced workflow. |
| Baseline, implemented and evaluated | One OpenAI-compatible structured completion receives the frozen dossier and scenario. It writes draft actions only, has no tools, retries, memory, verifier, human-feedback loop, or life-safety estimator. A deterministic evaluator checks response structure, evidence IDs, policy patterns, and LSAC@5 from explicit human adjudication. | Final run: `runs/baseline/nepal-emsr927-v1.run.json`. Human review: `runs/baseline/nepal-emsr927-v1.adjudication.json`. Completed evaluator report: `runs/baseline/nepal-emsr927-v1.evaluation.json`. Result: one credentialed `gpt-5-mini-2025-08-07` run, five actions, LSAC@5 `3/17` (`17.65%`), unsafe autonomous actions `0`, missing evidence references `0`, valid references `9`, runtime `40.92s`, tokens `1,702` prompt and `1,950` completion, cost not captured. Verification: `uv run pytest` reported `21 passed in 0.14s`. Execution record: `docs/execution/2026-08-30-03-nepal-baseline-evaluation.md`. | Keep as the fair direct-prompt baseline. It is safe by the implemented policy checks but weak at location-specific operational coverage: generic Rasuwa and Trishuli actions missed Timure access, Bidur residential triage, and Syapru Besi critical-services continuity. Iteration 1 must retrieve and verify AOI-specific evidence before action drafting. |
| Documentation maintenance | Added the Micro1 submission entry-point README, a maintained Markdown version of the supplied hackathon brief, and explicit project-skill requirements to keep README evidence and commands current. Removed the local no-mistakes gate instructions at the user's request. | `README.md`; `docs/micro1-hackathon-brief.md`; `docs/execution/2026-08-30-01-readme-and-skill-maintenance.md`. No product metric changed. | Keep. The README must remain aligned with reproducible commands, current evidence, and truthful benchmark status. |
| Baseline compatibility correction | A credentialed `gpt-5-mini` call failed because the gateway sent unsupported `temperature: 0`. Removed that parameter, added a payload regression test, and split saved-run scoring into `climate-cascade-evaluate-baseline` so manual adjudication never triggers another model call. | Initial model call: HTTP `400`; focused contract and evaluator tests passed. The post-fix credentialed run then completed and is recorded in the baseline implementation row. | Keep. The compatibility repair enabled the measured baseline rather than changing its capability. |
| Durable workflow foundation, implemented | Added Alembic-managed SQLite tables for runs, ordered events, immutable artifacts, and run-artifact links; a SHA-256 content-addressed artifact store; FastAPI run creation, status, SSE, and baseline-artifact endpoints; and a separate worker with atomic SQLite leases and explicit baseline state transitions. | Focused persistence/API/worker tests cover migration application, idempotency, ordered SSE replay, expired-lease reclaim, API-created baseline execution, immutable artifacts, and pause at human review. Full verification: `uv run pytest` reported `26 passed in 0.46s`; API and worker CLI help commands loaded; `uv lock --check` passed. No agent-quality evaluation was run because agent-mode runs deliberately block until Iteration 1 source verification exists. Evidence: `docs/execution/2026-08-30-04-durable-workflow-api-and-worker.md`; `backend/tests/test_workflow_api.py`. | Keep. This makes the future agent observable and resumable without turning the persistence or worker into an agent. The next change must implement verified AOI-specific source intake and rerun the same frozen evaluation. |
| Local runtime reproducibility, implemented | Added a `climate-cascade-local` command with `init` and `serve` subcommands. SQLite parent directories are now created by the persistence layer before connection or migration, so a clean checkout can initialize `var/climate-cascade.db` through `uv run` without hidden setup. `serve` starts the FastAPI API and a local worker against the same SQLite database and artifact root. | Focused tests in `backend/tests/test_local_runtime.py` cover local SQLite/tables/artifact-root creation and API-plus-worker startup wiring. Full verification: `uv run pytest` reported `28 passed in 0.49s`; CLI help, local `init`, health-checkable local server smoke, `uv lock --check`, `compileall`, and `git diff --check` passed. Evidence: `docs/execution/2026-08-30-05-local-runtime-sqlite-setup.md`. No agent-quality evaluation was run. | Keep. This strengthens the Micro1 reproducibility path and makes the local control plane easier for a reviewer to run before source adapters and the dashboard are implemented. |
| Iteration 1a: verified CEMS source intake and dashboard, completed | Added a typed CEMS Rapid Mapping adapter, canonical SHA-256 snapshots, source metadata and license fields, claim and finding contracts, AOI product/data-gap handling, agent source-intake transitions, stored evidence endpoint, and a local dashboard that shows durable worker progress and source evidence. | [Execution record](../execution/2026-08-30-06-iteration-1-source-intake-dashboard.md); [live run summary](../../runs/iteration_1/iteration1-source-round-summary.json); individual run/evidence/SSE artifacts in `runs/iteration_1/`; full verification `uv run pytest`: `37 passed` (one upstream TestClient deprecation warning). Nepal `EMSR927` was `preliminary` with two pending products; closed `EMSR756` and `EMSR851` were `supported` without source-level data gaps. | Keep as a source-intake checkpoint. It preserves freshness and incompleteness instead of flattening every activation into a verified event. It is not action-quality evidence. |
| Iteration 1b: bounded response supervisor and review dashboard, implemented | Continued the original Iteration 1 lifecycle: one configured structured-output response supervisor receives compact verified evidence and scenario constraints, returns at most five cited drafts, and cannot access raw source payloads or frozen gold actions. The worker records the supervisor trajectory, deterministically checks action safety and evidence IDs, produces a human-adjudicable report, and reaches `awaiting_human_review`. The dashboard now explains inputs for non-technical analysts, offers CEMS examples and official product links, shows AOI availability honestly, draft actions, evaluation state, and recent local runs. | `backend/tests/test_response_supervisor.py`; `backend/tests/test_workflow_api.py`; [agent evaluation guide](../evaluation/agent.md); [execution record](../execution/2026-08-31-07-iteration-1-response-supervisor-dashboard.md). Full regression verification is recorded in that execution record. Contract tests use a static gateway and do not measure model quality. | Keep the implementation. The required next evidence is one credentialed frozen Nepal supervisor run plus human adjudication. Do not claim a score, improvement, or life-safety benefit until those artifacts exist. The next architecture capability remains deterministic AOI impact and spatial overlays, followed later by an independent evidence supervisor. |
| Local `.env` reproducibility, implemented | Added project-local `.env` loading to the baseline, evaluator, API, worker, and combined local-server commands. The loader is optional, ignores missing files, respects an explicitly exported variable, and `.gitignore` excludes `.env`; `.env.example` remains the safe committed template. | `backend/tests/test_environment.py`; [execution record](../execution/2026-08-31-08-local-dotenv-loading.md); `README.md`; `.env.example`. This is a setup improvement, not a model or evaluation result. | Keep. A user can now paste their real API key once into ignored `.env` and restart the dashboard normally. |
| Iteration 2, planned | Add deterministic population, asset, and road-connectivity calculations. | Not run. | Test population error, asset F1, and duplicate-population rate. |
| Iteration 3, planned | Add typed action templates, ranking, ownership, dependencies, and an evidence verifier. | Not run. | Test LSAC@5 and unsupported-action rate. |
| Iteration 4, planned | Add potential-lives-saved ranges, editable assumptions, and approve/edit/reject/request-evidence feedback. | Not run. | Test interval coverage, abstention, safety, and review time. |

## Baseline Final Findings

This is the final measured direct-prompt baseline record for the current Nepal challenging case. It is the comparison point for later iterations, not evidence that the future agent improves the outcome.

- **Case and run:** `nepal-emsr927-v1`, `baseline-0cc0c424-df31-4897-8248-a81f3890c3a3`
- **Model and scope:** one `gpt-5-mini-2025-08-07` structured completion, five unapproved draft actions, no tools, retrieval, memory, retries, verifier, geospatial computation, or life-safety estimator.
- **Primary result:** LSAC@5 `3/17` (`17.65%`).
- **Covered requirement:** Bharatpur was correctly retained as an unknown pending area with an evidence request.
- **Missed requirements:** access verification near Timure; residential-impact triage in Bidur; critical-services continuity near Syapru Besi.
- **Safety and evidence:** `0` unsafe autonomous-action findings, `0` missing evidence references, `9` valid evidence references.
- **Resources:** `40.92s` runtime; `1,702` prompt tokens and `1,950` completion tokens; provider cost not captured.
- **Interpretation:** generic district and corridor actions can look plausible but do not satisfy location-specific life-safety requirements. Iteration 1 must test whether verified AOI-specific evidence retrieval and typed action planning raise LSAC@5 without introducing unsafe actions.
- **Evidence:** `runs/baseline/nepal-emsr927-v1.run.json`, `runs/baseline/nepal-emsr927-v1.adjudication.json`, `runs/baseline/nepal-emsr927-v1.evaluation.json`, and `docs/execution/2026-08-30-03-nepal-baseline-evaluation.md`.

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
