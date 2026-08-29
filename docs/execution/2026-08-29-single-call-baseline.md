# Execution Record: Single-Call Baseline and Evaluation Output

Date: 2026-08-29
ADR step: 2 - Implement the single-call baseline and evaluation output
Branch: `baseline`

## Acceptance criteria

- A frozen case produces one structured baseline-model request and preserves its exact output.
- The baseline has no tools, memory, retries, verifier, human-feedback loop, or life-safety estimator.
- Missing configuration, provider failure, schema failure, and unknown evidence references fail closed into durable artifacts.
- The evaluator calculates LSAC@5 only from complete, explicit human coverage adjudication.
- The evaluator records deterministic policy findings without modifying the raw model output.
- The CLI writes both run and evaluation JSON in success and failure paths.

## Implemented artifacts

- `backend/src/climate_cascade/baseline/` - prompt rendering, one-call provider boundary, runner, and run artifact.
- `backend/src/climate_cascade/evaluation/scoring.py` - transparent metrics, human coverage adjudication, LSAC@5, and policy findings.
- `backend/src/climate_cascade/cli.py` - local command that writes run and evaluation JSON.
- `docs/evaluation/baseline.md` - live-run, adjudication, and placeholder protocol.

## Commands and results

```bash
uv run pytest backend/tests/test_baseline_runner.py backend/tests/test_baseline_evaluation.py backend/tests/test_baseline_cli.py
```

Result: `9 passed in 1.29s`.

```bash
uv run pytest
uv run python -m compileall -q backend/src
uv lock --check
```

Result: full suite `19 passed in 0.11s`; source compilation passed; the lockfile check passed.

```bash
uv run climate-cascade-baseline \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --model verification-model \
  --output var/verification/baseline-nepal-no-provider.run.json \
  --evaluation-output var/verification/baseline-nepal-no-provider.evaluation.json
```

Result: expected exit status `2`; the command wrote a `provider_not_configured` run artifact and a `run_failed` evaluation artifact. No network request was attempted because `OPENAI_API_KEY` was absent. This verifies the fail-closed local path. It is not a live-model benchmark run and supplies no performance metric.

## Findings and limitations

- The current environment has no configured model-provider key, so live model quality, token usage, latency, cost, and LSAC@5 remain unmeasured.
- The baseline evaluator requires human semantic matching of each proposal to every frozen gold action. This is deliberate: a second language model would create an untraceable model-grades-model metric.
- Policy matching is deterministic and intentionally narrow. It catches obvious prohibited patterns, not all unsafe or unsupported natural-language variants. Iteration 3 will add the independent evidence and safety supervisor required for richer verification.
- Nepal is an open challenging case. Its eventual score must be reported separately from closed-event accuracy aggregates.

## Decision

Keep the implementation. It provides a real, reproducible single-call baseline path and does not convert missing credentials into a synthetic benchmark result. The next prerequisite for measured comparison is a credentialed Nepal run with a complete adjudication, followed by materialized closed CEMS benchmark fixtures.
