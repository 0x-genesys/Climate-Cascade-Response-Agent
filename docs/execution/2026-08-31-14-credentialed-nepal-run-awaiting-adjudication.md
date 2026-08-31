# Credentialed Nepal Run Awaiting Adjudication

- **Date and sequence:** 2026-08-31, record 14
- **Scope:** Iteration 1 credentialed response-supervisor run and evaluation-bundle preservation
- **ADR step:** Complete the bounded draft and deterministic checks, then stop at the required human review checkpoint.

## Run captured

The local dashboard created run `run-e7be6463-07d6-4b74-843f-db59897d0faf` for frozen case `nepal-emsr927-v1` using `gpt-5-mini-2025-08-07`. The worker reached `awaiting_human_review` after 14 durable events.

The stored deterministic report records:

- five draft-only actions;
- zero unsafe autonomous-action patterns;
- zero missing evidence references;
- seven valid evidence references;
- all action life-safety fields as `not_estimable`; and
- LSAC@5 as `not_evaluated`, with human coverage adjudication required.

## Evaluation bundle

The exact artifacts were preserved in `runs/iteration_1/`:

- `nepal-emsr927-response-supervisor.run.json`
- `nepal-emsr927-response-supervisor.evidence.json`
- `nepal-emsr927-response-supervisor.adjudication.json`

The adjudication file has the exact run ID and four required gold-action decisions, but its reviewer identity, timestamp, coverage decisions, action IDs, and rationales are deliberate placeholders. They are not evidence and must be replaced by the human reviewer.

## Validation

The local API was queried for the run, agent artifact, evidence package, and durable SSE trajectory. The response supervisor status was `completed`; the run state was `awaiting_human_review`; and the stored evaluator report was `not_evaluable` solely because adjudication was absent.

The persisted JSON files parse successfully:

```bash
jq empty runs/iteration_1/nepal-emsr927-response-supervisor.run.json
jq empty runs/iteration_1/nepal-emsr927-response-supervisor.evidence.json
jq empty runs/iteration_1/nepal-emsr927-response-supervisor.adjudication.json
```

## Next step

After the reviewer completes all four decisions, run:

```bash
uv run climate-cascade-evaluate-agent \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run runs/iteration_1/nepal-emsr927-response-supervisor.run.json \
  --evidence runs/iteration_1/nepal-emsr927-response-supervisor.evidence.json \
  --adjudication runs/iteration_1/nepal-emsr927-response-supervisor.adjudication.json \
  --evaluation-output runs/iteration_1/nepal-emsr927-response-supervisor.evaluation.json
```

Only that deterministic output can establish whether this run improves on the baseline LSAC@5 `3/17`.
