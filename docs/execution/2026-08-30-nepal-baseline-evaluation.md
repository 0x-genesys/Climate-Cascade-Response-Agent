# Nepal Baseline Evaluation

Date: 2026-08-30
Sequence: 03

ADR step: 2 - Implement the single-call baseline and evaluation output

## Purpose

Record the first successful credentialed baseline run and completed human adjudication for the frozen Nepal `EMSR927` challenging case. This is a single difficult open-event case, not a closed-event aggregate and not evidence of agent improvement.

## Artifacts

- Run: `runs/baseline/nepal-emsr927-v1.run.json`
- Human adjudication: `runs/baseline/nepal-emsr927-v1.adjudication.json`
- Evaluation: `runs/baseline/nepal-emsr927-v1.evaluation.json`

## Commands

```bash
uv run climate-cascade-evaluate-baseline \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run runs/baseline/nepal-emsr927-v1.run.json \
  --adjudication runs/baseline/nepal-emsr927-v1.adjudication.json \
  --evaluation-output runs/baseline/nepal-emsr927-v1.evaluation.json
```

## Result

- Model: `gpt-5-mini-2025-08-07`
- Provider: OpenAI
- Model attempts: `1`
- Draft actions: `5`
- Runtime: `40.92s`
- Tokens: `1,702` prompt and `1,950` completion
- Cost: not captured
- LSAC@5: `3/17` (`17.65%`)
- Unsafe autonomous-action patterns: `0`
- Missing evidence references: `0`
- Valid evidence references: `9`

The human adjudicator credited only `act-003-request-bharatpur-aoi`, because it retained Bharatpur as a pending data gap and requested evidence. The baseline did not meet the frozen requirements for access verification near Timure, residential-impact triage in Bidur, or a critical-services continuity check near Syapru Besi.

## Decision

Keep this result as the direct-prompt baseline. The next iteration must test whether verified, AOI-specific evidence retrieval and typed action planning improve life-safety action coverage while preserving the zero unsafe-action finding.
