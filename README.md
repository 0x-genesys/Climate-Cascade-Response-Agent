# Climate Cascade Response Agent

## Keep Four Questions In Mind

### 01. Who Has This Problem?

### 02. What Bottleneck Makes It Worth Solving?

### 03. Does The Agent Solve It Well?

### 04. Can Another Person Reproduce The Result?

Climate Cascade Response turns a verified post-disaster flood or debris-flow case into a short, evidence-backed queue of actions for an emergency operations analyst. The analyst keeps authority: every action remains a draft for human review, and the product never sends public warnings, dispatches responders, or controls infrastructure.

## The problem

Damage maps and situation reports do not answer the operational questions an emergency manager must resolve next: which community needs attention first, what evidence supports that priority, what is still unknown, and who must approve the action. The MVP organizes that evidence into reviewable action proposals while preserving data gaps and uncertainty.

The pilot case is Nepal `EMSR927`. It is a deliberately difficult, evolving event with a pending AOI and unresolved trigger details. It demonstrates uncertainty handling, not closed-event accuracy. The hackathon MVP is limited to floods and debris flows. Earthquakes, tsunamis, tornadoes, and volcanic eruptions are roadmap hazards that require their own adapters and benchmarks.

## Current status

ADR steps 2 through 7 are implemented. The baseline makes one structured model call over the checksum-verified Nepal fixture, records the exact response, and produces an evaluation artifact. A SQLite-backed FastAPI control plane queues runs, exposes ordered SSE progress, and a separate leased worker persists artifacts. Iteration 1 adds a typed CEMS source adapter, immutable evidence package, one bounded response-supervisor call, deterministic draft checks, a human-adjudicable evaluation path, and a plain-language dashboard. Iteration 2 adds a deterministic CEMS product-statistics impact package: it selects one newest finished product per AOI, extracts source-reported population, buildings, facilities, roads, bridges, and coverage gaps, prevents duplicate product-version sums, and gives only the compact cited result to the supervisor. Iteration 4 adds versioned human-review audit records and visible `not_estimable` abstentions. It does not yet perform local raster/vector geometry overlays or numeric life-safety estimation, and a recorded decision never dispatches or executes an action.

One credentialed Nepal baseline is recorded: `gpt-5-mini-2025-08-07` produced five draft actions, and human adjudication measured LSAC@5 at `3/17` (`17.65%`). The run had zero deterministic unsafe-action findings and zero missing evidence references. This is one difficult, open-event case, not a closed-event aggregate or evidence of improvement. Model cost is not recorded. The implementation and result are documented in [the baseline evaluation guide](docs/evaluation/baseline.md) and [execution ledger](docs/execution/2026-08-30-03-nepal-baseline-evaluation.md).

Iteration 1 is finalized as a **live Nepal proof of concept**, not a fair improvement benchmark. A live `EMSR927` run retrieved current CEMS AOI metadata, generated four human-review-only actions, and passed automatic checks: `0` unsafe autonomous-action findings, `0` missing evidence references, and `4` valid references. A project-owner, AI-assisted rubric-transfer review covered Bharatpur only: LSAC@5 `3/17` (`17.65%`). It cannot be compared as an uplift or regression against the frozen baseline because CEMS had changed since the baseline fixture. The result is useful because it exposes the next capability gap: AOI product-status metadata alone cannot produce the specific Timure, Bidur, and Syapru Besi actions. See [the agent evaluation guide](docs/evaluation/agent.md) and the [retained POC evidence bundle](runs/iteration_1/README.md).

Iteration 2 is finalized as a second **live Nepal proof of concept**. Its retained `gpt-5-mini-2025-08-07` run used CEMS product statistics to draft five cited actions. Project-owner, AI-assisted rubric transfer measured LSAC@5 `13/17` (`76.47%`), covering Timure access, Bidur residential triage, and Bharatpur's data gap, while missing Syapru Besi critical-services continuity. Automatic checks remained at `0` unsafe autonomous-action findings, `0` missing evidence references, and `5` valid references. This is not a baseline uplift claim: the run uses mutable live CEMS data, a project-owner reviewer, and a new prompt/resource profile. It is evidence that compact deterministic product facts materially improved location specificity while exposing the remaining action-selection trade-off. See [the agent evaluation guide](docs/evaluation/agent.md) and the [retained Iteration 2 bundle](runs/iteration_2/README.md).

## Quick start

Prerequisites:

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key only for a live baseline model call

Install the project and run the complete test suite:

```bash
uv sync --group dev
uv run pytest
```

Expected result: all contract, frozen-fixture, baseline-runner, evaluator, local-runtime, API, worker, and CLI tests pass. Tests use a local static gateway and do not consume an API key or provide model-quality evidence.

Initialize the local SQLite runtime:

```bash
uv run climate-cascade-local init
```

Expected result: the command creates `var/climate-cascade.db`, applies the checked-in Alembic migrations, and prepares `var/artifacts/`.

## Configure an OpenAI API key

The live baseline and dashboard worker read `OPENAI_API_KEY` from a local `.env` file or the process environment. Do not commit a key, put it in fixtures, or include it in an execution artifact.

```bash
cp .env.example .env
```

Edit `.env` and replace the empty value with your real key:

```dotenv
OPENAI_API_KEY=sk-your-real-key
```

Every project CLI command loads `.env` from the current project directory automatically. A value explicitly exported by your shell or CI takes precedence over `.env`. The dashboard never receives or displays the key.

You can use a different environment-variable name with `--api-key-env YOUR_VARIABLE_NAME`.

## Run the baseline

Choose a structured-output model available to your OpenAI account and run exactly one baseline attempt. `gpt-5-mini` uses the provider default temperature, so the baseline does not send a `temperature` parameter.

```bash
uv run climate-cascade-baseline \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --model gpt-5-mini \
  --output var/runs/nepal-baseline.run.json \
  --evaluation-output var/runs/nepal-baseline.initial-evaluation.json
```

The command writes both JSON artifacts. Exit `0` means the response met the output contract. Exit `2` means it recorded a fail-closed result such as missing credentials, provider failure, schema failure, or an unknown evidence ID. Do not retry a failed call within the same benchmark run.

LSAC@5 requires an explicit human coverage-adjudication file that maps every frozen gold action to a proposed action or marks it uncovered. Score the saved run without another model call:

```bash
uv run climate-cascade-evaluate-baseline \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run var/runs/nepal-baseline.run.json \
  --adjudication var/runs/nepal-baseline.adjudication.json \
  --evaluation-output var/runs/nepal-baseline.evaluation.json
```

The exact four-decision template and evaluation semantics are in [docs/evaluation/baseline.md](docs/evaluation/baseline.md).

## Run The Control Plane

The fastest local path starts the API and a worker in one process against the same SQLite database:

```bash
uv run climate-cascade-local serve
```

Open `http://127.0.0.1:8000/` for the incident dashboard, or `http://127.0.0.1:8000/v1/health` and expect `{"status":"ready"}`. The dashboard never displays API keys. Enter the model name only, such as `gpt-5-mini`; the worker reads `OPENAI_API_KEY` from its environment.

For process-isolation testing, start the API and worker in separate terminals:

```bash
uv run climate-cascade-api \
  --database-url sqlite:///var/climate-cascade.db \
  --artifact-root var/artifacts
```

```bash
uv run climate-cascade-worker \
  --database-url sqlite:///var/climate-cascade.db \
  --artifact-root var/artifacts
```

Create a queued baseline run with an idempotency key. The worker makes the one model call only after it leases this run. It stores immutable run and evaluation artifacts under `var/artifacts/` and stops at `awaiting_human_review`.

```bash
curl -X POST http://127.0.0.1:8000/v1/baseline/runs \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: local-baseline-001' \
  -d '{"case_id":"nepal-emsr927-v1","model":"gpt-5-mini"}'
```

Use `GET /v1/runs/{run_id}`, `GET /v1/runs/{run_id}/events`, and `GET /v1/runs/{run_id}/baseline` to inspect durable status, reconnectable SSE progress, and saved baseline artifacts.

## Run Iteration 1 response review

Start the local control plane as above, set `OPENAI_API_KEY`, and open `http://127.0.0.1:8000/`. Choose a named live CEMS example for Nepal, South-west Poland, or Sri Lanka, or select its activation code directly. The dashboard explains what each example is useful for, distinguishes CEMS product coverage from a geographic map, links to official sources, and lets you inspect a prior local run from the dropdown.

```bash
curl -X POST http://127.0.0.1:8000/v1/agent/runs \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: live-emsr927-001' \
  -d '{"case_id":"emsr927","mode":"agent","fixture_mode":false,"activation":"EMSR927","model":"gpt-5-mini"}'
```

Copy `run_id` from the `202` response, then inspect the persisted progress and source-evidence package:

```bash
curl http://127.0.0.1:8000/v1/runs/RUN_ID
curl http://127.0.0.1:8000/v1/runs/RUN_ID/events?follow=false
curl http://127.0.0.1:8000/v1/runs/RUN_ID/evidence
curl http://127.0.0.1:8000/v1/runs/RUN_ID/impacts
curl http://127.0.0.1:8000/v1/runs/RUN_ID/agent
```

Expected behavior: Nepal `EMSR927` is currently `preliminary` because CEMS marks the activation open and records pending AOI products. A successful supervisor run becomes `awaiting_human_review`; `blocked` means the worker safely rejected an invalid source, absent model configuration, provider error, schema failure, or output-policy failure. Iteration 2 saves `/impacts`: source-reported CEMS product statistics for completed AOIs and explicit gaps, with one newest product version selected per AOI. Live runs show deterministic checks. A formal LSAC@5 benchmark needs a frozen case and qualified human adjudication; the retained Nepal POCs use clearly-labelled project-owner rubric transfer, not a comparable benchmark. Run `EMSR756` or `EMSR851` to inspect completed historical flood activations.

## Evaluation path

There are two intentionally separate paths. The baseline action-quality path is complete: run the one-call baseline, create the human adjudication file, then run `climate-cascade-evaluate-baseline` to calculate LSAC@5 and deterministic safety checks. That evaluator is deterministic and does not call an LLM.

Iteration 1 evaluates source handling and response drafting: the worker retrieves CEMS through the configured adapter, persists a typed evidence package, makes one bounded structured call, then deterministically checks draft safety and evidence IDs. The dashboard or `/evidence` and `/agent` endpoints expose source status, snapshot hash, AOI completeness, draft actions, explicit `not_estimable` reasons, and evaluation state. For the pinned case, use the human-adjudication process in [the agent evaluation guide](docs/evaluation/agent.md) to calculate LSAC@5 without another model call. Iteration 2 adds deterministic impact evidence and spatial overlays; an independent evidence supervisor, final action approval, and numeric life-safety estimates remain later work.

## Evidence and submission record

The [maintained Micro1 brief](docs/micro1-hackathon-brief.md) asks for a meaningful user problem, purposeful agent engineering, a realistic end-to-end result, measured improvement over a fair baseline, clean reproduction, and an observed insight. This repository maintains those artifacts as work proceeds:

- [Product plan](docs/product.md) - user, scope, safety boundary, data, and target outputs.
- [Architecture decision record](docs/architecture/ADR-0001-iterative-agentic-architecture.md) - baseline-to-final build order and agentic boundaries.
- [Evaluation plan](docs/evaluation/README.md) - LSAC@5, safety gates, closed-case benchmark, and challenging Nepal case.
- [Improvement changelog](docs/solution_improvement/README.md) - retained, revised, and removed experiments with evidence.
- [Project story](docs/story/README.md) - submission narrative, claims ledger, and eventual hot take.
- [Execution ledger](docs/execution/README.md) - exact commands, test outcomes, and limitations.

The final submission will also include representative trajectories for every agent, including instructions, tool responses, retries, verifier feedback, and human checkpoints. The current baseline is not an agent and has no tools or retries; its prompt and raw response are preserved in each run artifact instead.

## Reviewer Evidence

| Review focus | Evidence | What to verify |
| --- | --- | --- |
| Problem, user, scope, and safety boundary | [Product plan](docs/product.md) | Flood and debris-flow MVP only; actions remain human-reviewed drafts. |
| Architecture and iteration order | [ADR](docs/architecture/ADR-0001-iterative-agentic-architecture.md) | Direct-prompt baseline is distinct from the planned agentic workflow and its deterministic tools. |
| Frozen benchmark input | [Nepal fixture](data/fixtures/cases/nepal-emsr927-v1/README.md) | Cited, checksum-verified input with explicit uncertainty and synthetic operational constraints. |
| Live baseline trajectory | [Baseline evidence folder](runs/baseline/) and [saved run](runs/baseline/nepal-emsr927-v1.run.json) | One `gpt-5-mini-2025-08-07` call produced five unapproved actions. |
| Human semantic review | [Coverage adjudication](runs/baseline/nepal-emsr927-v1.adjudication.json) | Only Bharatpur's pending-data-gap action is covered; Timure, Bidur, and Syapru Besi remain missed. |
| Deterministic score and safety checks | [Evaluation report](runs/baseline/nepal-emsr927-v1.evaluation.json) and [evaluation guide](docs/evaluation/baseline.md) | LSAC@5 is `3/17` (`17.65%`); zero unsafe autonomous-action findings and zero missing evidence references. |
| Durable run control plane | [Workflow execution record](docs/execution/2026-08-30-04-durable-workflow-api-and-worker.md), [local runtime record](docs/execution/2026-08-30-05-local-runtime-sqlite-setup.md), [API package](backend/src/climate_cascade/api/), and [workflow package](backend/src/climate_cascade/workflow/) | `uv run` setup, SQLite migrations, idempotent run creation, ordered reconnectable SSE, immutable artifacts, worker leases, and baseline pause at human review. |
| Iteration 1 live POC, drafting, and dashboard | [Finalization record](docs/execution/2026-08-31-15-iteration-1-live-poc-finalization.md), [retained POC bundle](runs/iteration_1/README.md), [agent evaluation guide](docs/evaluation/agent.md), [source adapters](backend/src/climate_cascade/sources/), and [dashboard](dashboard/) | Current CEMS AOI metadata, one bounded response-supervisor call, deterministic draft checks, project-owner rubric-transfer review, and user-visible run feedback. Result: `3/17`, not comparable with the frozen baseline because source snapshots differ. |
| Iteration 2 deterministic impact POC | [Finalization record](docs/execution/2026-08-31-16-iteration-2-live-poc-finalization.md), [retained POC bundle](runs/iteration_2/README.md), [agent evaluation guide](docs/evaluation/agent.md), [impact engine](backend/src/climate_cascade/impacts/), and [dashboard](dashboard/) | Immutable CEMS product-statistics impact package, one newest finished product per AOI, product-version deduplication, source-reported population/assets/access facts, compact supervisor context, SSE progress, and dashboard impacts. Diagnostic rubric transfer: `13/17`; not comparable with the frozen baseline. |
| Reproducible execution history | [Execution ledger](docs/execution/README.md) and [final baseline record](docs/execution/2026-08-30-03-nepal-baseline-evaluation.md) | Records are sequenced in filenames and retain failed attempts alongside the successful result. |
| Measured baseline limitations and next hypothesis | [Improvement changelog](docs/solution_improvement/README.md) | The next iteration must improve AOI-specific life-safety coverage without losing safety or evidence performance. |
| Judge-facing narrative and claim limits | [Project story](docs/story/README.md) | No claim of final-agent improvement, lives saved, or multi-hazard validation is made before evidence exists. |
| Project operating rules | [Climate Cascade skill](.codex/skills/climate-cascade-response/SKILL.md) and [Micro1 build skill](.codex/skills/micro1-build/SKILL.md) | Major checkpoints require synchronized execution, evaluation, improvement, story, README, and architecture records. |

## Data and safety

The committed Nepal fixture contains cited public summaries and explicit synthetic operational constraints. It is checksum-verified before use. It does not include private data, raw operational control, or a claim that an action was taken.

Potential lives saved is not implemented in the baseline. Later work may produce only deterministic, sourced low-central-high counterfactual ranges or `not estimable`; it will never equate exposed population with observed lives saved.

## Repository layout

```text
backend/                  Python domain contracts, baseline, evaluation, API, persistence, and workflow worker
dashboard/                Local source-intake and worker-progress dashboard served by FastAPI
data/fixtures/            Checksum-verified frozen disaster cases
docs/                     Product, Micro1 brief, architecture, evaluation, execution, story, and changelog
var/artifacts/            Local content-addressed artifacts, excluded from version control
var/climate-cascade.db    Local SQLite workflow database, excluded from version control
var/                      Local generated run artifacts, excluded from version control
```
