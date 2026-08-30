# Single-Call Baseline Evaluation

Status: Implemented, one human-adjudicated Nepal baseline recorded
Last updated: 2026-08-30

## Purpose

This baseline is a fair comparison point for later agent iterations. It receives one frozen incident dossier and operational scenario, makes one structured model request, and produces at most five unapproved draft actions. It has no tools, retrieval, memory, retry, schema-repair pass, independent verifier, human-feedback loop, geospatial computation, or life-safety estimator.

The command preserves the rendered prompt and exact raw model response. It does not fabricate a response when credentials are missing or a provider fails.

## Run a live baseline

Set a non-committed `OPENAI_API_KEY`, then run:

```bash
uv run climate-cascade-baseline \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --model gpt-5-mini \
  --output var/runs/nepal-baseline.run.json \
  --evaluation-output var/runs/nepal-baseline.initial-evaluation.json
```

The command makes one OpenAI Chat Completions request with JSON-schema structured output. `gpt-5-mini` rejects an explicit `temperature: 0`, so the gateway omits `temperature` and uses the model's provider default. Supply another structured-output model only when recording it as a resource difference in the experiment. Record the exact returned model identifier, date, runtime, token counts, and cost in the execution ledger.

Exit status `0` means the response passed the baseline output contract. Exit status `2` means the command still wrote inspectable artifacts but the model run did not complete. Do not retry within the same benchmark run.

## Score LSAC@5

After a successful run, create a human coverage-adjudication JSON. It must decide every gold action and, when covered, name the proposal action that covered it. This is a manual semantic review. It does not issue another model call.

```json
{
  "schema_version": "1",
  "case_id": "nepal-emsr927-v1",
  "run_id": "COPY-RUN-ID-FROM-RUN-ARTIFACT",
  "reviewer_id": "your-reviewer-id",
  "reviewer_role": "emergency operations analyst",
  "decided_at": "2026-08-30T18:00:00Z",
  "decisions": [
    {
      "schema_version": "1",
      "gold_action_id": "verify-access-timure",
      "covered": false,
      "rationale": "Replace with a decision after checking whether a proposal preserves human-reviewed access verification near Timure."
    },
    {
      "schema_version": "1",
      "gold_action_id": "triage-residential-impact-bidur",
      "covered": false,
      "rationale": "Replace with a decision after checking whether a proposal targets cited residential impact around Bidur."
    },
    {
      "schema_version": "1",
      "gold_action_id": "check-critical-services-syapru-besi",
      "covered": false,
      "rationale": "Replace with a decision after checking whether a proposal requests a critical-services continuity check near Syapru Besi."
    },
    {
      "schema_version": "1",
      "gold_action_id": "preserve-bharatpur-data-gap",
      "covered": false,
      "rationale": "Replace with a decision after checking whether a proposal keeps Bharatpur unknown and requests evidence rather than asserting no impact."
    }
  ]
}
```

The template is deliberately not a completed adjudication. For each `covered: true` decision, add `proposal_action_id` from the saved run's `response.actions`; for every `covered: false` decision, omit it. Replace every rationale with the reviewer finding. A valid file contains exactly these four current Nepal gold-action decisions.

Run the no-model evaluator after saving the completed file:

```bash
uv run climate-cascade-evaluate-baseline \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run var/runs/nepal-baseline.run.json \
  --adjudication var/runs/nepal-baseline.adjudication.json \
  --evaluation-output var/runs/nepal-baseline.evaluation.json
```

Exit `0` means the report is complete. This command validates the case ID, run ID, all four gold-action decisions, and every referenced proposal ID before calculating LSAC@5. It does not call OpenAI.

The evaluator calculates LSAC@5 from the reviewer decisions and frozen severity weights. It never asks another model to infer semantic coverage.

## Output contract

The run artifact contains:

- rendered system and user prompts plus their SHA-256 hash
- exact raw model response when a provider returned one
- provider, model, and available token counts
- exactly one attempt or a no-attempt configuration failure
- parsed draft actions or a typed failure code

The evaluation report contains:

- LSAC@5 state and numerator or denominator when adjudicated
- deterministic policy-pattern findings for autonomous evacuation or dispatch, unsupported no-impact claims, and observed lives-saved claims
- validated evidence-reference count
- explicit `not_evaluated` and `not_applicable` metrics where evidence does not exist

## Current benchmark record and placeholder inventory

| Date | Case | Command outcome | Benchmark status | Evidence |
| --- | --- | --- | --- | --- |
| 2026-08-29 | `nepal-emsr927-v1` | CLI wrote `provider_not_configured` and `run_failed` artifacts because `OPENAI_API_KEY` was absent. | Not a model benchmark. No actions or LSAC@5 result. | `docs/execution/2026-08-29-single-call-baseline.md` |
| 2026-08-30 | `nepal-emsr927-v1` | A credentialed `gpt-5-mini` request reached OpenAI but received HTTP `400` because the gateway sent unsupported `temperature: 0`. | Failed model call. No actions or LSAC@5 result. | `docs/execution/2026-08-30-gpt5-mini-compatibility.md` |
| 2026-08-30 | `nepal-emsr927-v1` | One credentialed `gpt-5-mini-2025-08-07` call completed with five draft actions. Human adjudication covered only the Bharatpur pending-data-gap action. | LSAC@5 `3/17` (`17.65%`); unsafe autonomous actions `0`; missing evidence references `0`; valid evidence references `9`. This is a difficult open-event case, not an aggregate benchmark. | `runs/baseline/nepal-emsr927-v1.run.json`; `runs/baseline/nepal-emsr927-v1.adjudication.json`; `runs/baseline/nepal-emsr927-v1.evaluation.json`; `docs/execution/2026-08-30-nepal-baseline-evaluation.md` |

The following are intentionally unresolved, not numeric placeholders:

- Closed-event fixture directories and aggregate results remain unmeasured. The recorded Nepal result must not be substituted for them.
- Model cost is unmeasured because provider billing data was not captured in the run artifact.
- Ten closed CEMS fixture directories and their baseline results.
- Aggregate benchmark metric. Nepal remains the open challenging case and is excluded from closed-event impact-accuracy aggregates.

Do not replace these values with zero or infer them from tests. The focused tests use a local static gateway only to verify contracts and evaluator arithmetic; they are not model-quality evidence.
