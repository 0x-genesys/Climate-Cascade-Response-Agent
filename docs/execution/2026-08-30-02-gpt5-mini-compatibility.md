# Execution Record: GPT-5 Mini Compatibility and Manual Adjudication

Date: 2026-08-30
Sequence: 02
Branch: `iteration_1`
Scope: repair the credentialed baseline failure, preserve the result, and separate manual scoring from model execution.

## Observed failure

The initial credentialed command used `gpt-5-mini` and wrote a `provider_error` artifact:

```text
Unsupported value: 'temperature' does not support 0 with this model.
Only the default (1) value is supported.
```

The failure occurred before the model returned an action response. It therefore produced no model tokens, actions, policy findings, or LSAC@5 score. The original artifacts remain at `var/runs/nepal-baseline.run.json` and `var/runs/nepal-baseline.evaluation.json` in the local workspace.

## Change

- Removed the explicit `temperature: 0` parameter from the OpenAI Chat Completions payload. The selected model now uses its supported provider default.
- Added an outbound-payload regression test that fails if `temperature` is sent again.
- Added `climate-cascade-evaluate-baseline`, which scores an existing saved run with a completed human adjudication file and does not call a model.
- Removed the confusing `--adjudication` option from `climate-cascade-baseline` so scoring cannot accidentally create a second model run.

## Verification

```bash
uv run pytest backend/tests/test_baseline_runner.py backend/tests/test_baseline_evaluation.py backend/tests/test_baseline_cli.py
uv run climate-cascade-baseline --help
uv run climate-cascade-evaluate-baseline --help
```

Result: focused suite passed after the change. The evaluator CLI accepts a case, existing run, human adjudication, and output path.

The isolated implementation worktree did not inherit `OPENAI_API_KEY`, so its attempted post-fix command produced `provider_not_configured` with `attempt_count: 0`. That is not a live validation of the repaired request. Run the documented command from the credentialed user shell to produce the first valid model result.

## Manual adjudication procedure

1. Run `climate-cascade-baseline` once and require exit status `0`.
2. Open the saved run artifact and copy its `run_id` plus the IDs in `response.actions`.
3. Create the four-decision JSON file documented in `docs/evaluation/baseline.md`.
4. Mark an action covered only when it satisfies the gold outcome, correct location or population, required time window, evidence consistency, and retained human authority.
5. Run `climate-cascade-evaluate-baseline` against the saved artifact. This performs no provider call and writes the LSAC@5 report.

## Result status

The request compatibility defect is fixed and regression-tested. The first credentialed post-fix baseline output, human adjudication, numeric LSAC@5, model token count, runtime, and cost remain unmeasured.
