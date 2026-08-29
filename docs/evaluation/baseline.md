# Single-Call Baseline Evaluation

Status: Implemented, no credentialed benchmark result recorded yet
Last updated: 2026-08-29

## Purpose

This baseline is a fair comparison point for later agent iterations. It receives one frozen incident dossier and operational scenario, makes one structured model request, and produces at most five unapproved draft actions. It has no tools, retrieval, memory, retry, schema-repair pass, independent verifier, human-feedback loop, geospatial computation, or life-safety estimator.

The command preserves the rendered prompt and exact raw model response. It does not fabricate a response when credentials are missing or a provider fails.

## Run a live baseline

Set a non-committed `OPENAI_API_KEY`, then run:

```bash
uv run climate-cascade-baseline \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --model YOUR_STRUCTURED_OUTPUT_MODEL \
  --output var/runs/nepal-baseline.run.json \
  --evaluation-output var/runs/nepal-baseline.evaluation.json
```

The command makes one OpenAI Chat Completions request with JSON-schema structured output. Supply a model that your account can use with structured outputs. The selected model is an input to the experiment, not a project-wide default. Record its exact identifier, date, runtime, token counts, and cost in the execution ledger.

Exit status `0` means the response passed the baseline output contract. Exit status `2` means the command still wrote inspectable artifacts but the model run did not complete. Do not retry within the same benchmark run.

## Score LSAC@5

After a successful run, create a human coverage-adjudication JSON. It must decide every gold action and, when covered, name the proposal action that covered it.

```json
{
  "schema_version": "1",
  "case_id": "nepal-emsr927-v1",
  "run_id": "baseline-REPLACE-WITH-RUN-ID",
  "reviewer_id": "benchmark-reviewer",
  "reviewer_role": "emergency operations analyst",
  "decided_at": "2026-08-29T18:00:00Z",
  "decisions": [
    {
      "schema_version": "1",
      "gold_action_id": "verify-access-timure",
      "covered": true,
      "proposal_action_id": "REPLACE-WITH-PROPOSAL-ACTION-ID",
      "rationale": "Explain the protective outcome, location, time window, evidence, and retained human authority."
    }
  ]
}
```

The example is intentionally incomplete and is not a valid adjudication. It is a field template only. A valid file must contain exactly the four current Nepal gold-action decisions. Rerun the command with `--adjudication path/to/adjudication.json` to produce a complete LSAC@5 report.

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

The following are intentionally unresolved, not numeric placeholders:

- Live Nepal baseline output, model identifier, tokens, latency, cost, and LSAC@5.
- Independent reviewer adjudication for any live baseline output.
- Ten closed CEMS fixture directories and their baseline results.
- Aggregate benchmark metric. Nepal remains the open challenging case and is excluded from closed-event impact-accuracy aggregates.

Do not replace these values with zero or infer them from tests. The focused tests use a local static gateway only to verify contracts and evaluator arithmetic; they are not model-quality evidence.
