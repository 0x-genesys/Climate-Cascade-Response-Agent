# Iteration 1 Response-Supervisor Evaluation

Status: One credentialed Nepal run passed automatic checks; human action-quality adjudication pending
Last updated: 2026-08-31

## What this evaluates

An Iteration 1 run performs three separate checks:

1. The response supervisor makes one structured model call from a saved, verified evidence package.
2. The application deterministically checks draft-action evidence IDs and unsafe autonomous-action language.
3. A human reviewer decides whether each frozen Nepal gold action is covered. Only then can the deterministic CLI calculate LSAC@5.

The CLI never calls an LLM. A score is not available for live CEMS activation runs because they have no frozen gold-action set.

## Dashboard versus score

The **Run Feedback** dashboard panel is an automatic pre-review only. After a successful run it shows deterministic action-safety and snapshot-reference checks, then says that human coverage review is next. It does not collect reviewer decisions and does not calculate LSAC@5 in the browser.

The final comparable score is the local CLI report after a reviewer completes the adjudication JSON. This separation keeps the semantic judgement explicit and prevents a second model or dashboard shortcut from silently deciding whether an action covered a gold requirement.

The dashboard also consumes the persisted run SSE stream to show observable lifecycle updates such as source intake, constrained draft generation, receipt of the structured response, and deterministic checks. It does not show token streaming or private model reasoning. The completed structured response is retained in the supervisor-run artifact; action cards appear only after the output contract accepts it.

## Start and inspect a practice run

Set `OPENAI_API_KEY`, start the local service, then select **Nepal flood practice case** in the dashboard and enter a structured-output model such as `gpt-5-mini`. The run should finish as `Ready for human review`, not `blocked`.

Save the two durable artifacts from the local API. Replace `RUN_ID` with the dashboard run ID.

```bash
mkdir -p var/runs/iteration_1
curl -s http://127.0.0.1:8000/v1/runs/RUN_ID/agent \
  | jq '.response_supervisor_run' > var/runs/iteration_1/nepal-response-supervisor.run.json
curl -s http://127.0.0.1:8000/v1/runs/RUN_ID/evidence \
  | jq '.source_evidence_package' > var/runs/iteration_1/nepal-response-supervisor.evidence.json
```

Read `response.actions` in `nepal-response-supervisor.run.json`. Each action's `action_id` is the only valid value for a covered decision's `proposal_action_id`. The action evidence chips are immutable source `snapshot_id` values, such as `cems-activation-snapshot`; they are checked automatically before human adjudication.

The supervisor prompt names those snapshot IDs explicitly. If a provider instead returns the corresponding source ID such as `cems-activation`, the application records the raw response but normalizes the persisted action citation to the one immutable snapshot ID before deterministic checking. Any ID that is neither a known snapshot ID nor a known source alias still fails closed.

## Recorded run awaiting adjudication

Run `run-e7be6463-07d6-4b74-843f-db59897d0faf` used `gpt-5-mini-2025-08-07` against the frozen Nepal practice case. It produced five draft actions and reached `awaiting_human_review`. Automatic checks found `0` unsafe autonomous-action patterns, `0` missing evidence references, and `7` valid snapshot references. All five life-safety fields correctly abstained as `not_estimable`.

The saved [supervisor run](../../runs/iteration_1/nepal-emsr927-response-supervisor.run.json), [evidence package](../../runs/iteration_1/nepal-emsr927-response-supervisor.evidence.json), and [human adjudication file](../../runs/iteration_1/nepal-emsr927-response-supervisor.adjudication.json) are the evaluation bundle. The LSAC@5 field remains `not_evaluated`; do not compare this run with the baseline `3/17` until the reviewer replaces all placeholder decisions and runs the deterministic evaluator.

## Record human coverage

Copy the template, replace every placeholder, and make exactly one decision for each gold action. A covered decision must cite an action ID from the saved supervisor run. An uncovered decision must omit `proposal_action_id`.

```bash
cp docs/evaluation/agent-adjudication.template.json \
  var/runs/iteration_1/nepal-response-supervisor.adjudication.json
```

The reviewer evaluates the proposed action, not the fluency of the explanation. A gold action is covered only if it has the intended protective outcome, correct location or population, required time window, non-contradicted evidence, and retained human authority.

## Calculate the report

```bash
uv run climate-cascade-evaluate-agent \
  --case data/fixtures/cases/nepal-emsr927-v1 \
  --run var/runs/iteration_1/nepal-response-supervisor.run.json \
  --evidence var/runs/iteration_1/nepal-response-supervisor.evidence.json \
  --adjudication var/runs/iteration_1/nepal-response-supervisor.adjudication.json \
  --evaluation-output var/runs/iteration_1/nepal-response-supervisor.evaluation.json
```

Exit `0` means the report is complete. The report includes LSAC@5, deterministic safety findings, and evidence-reference checks. It is comparable with the recorded baseline only when the same frozen case and all four adjudication decisions are present. Record model identifier, timestamps, token counts, runtime, cost if available, and the resulting JSON paths in the execution ledger before claiming an improvement.

## Important limits

- A static gateway passing contract tests proves the implementation, not model quality.
- Live CEMS runs receive deterministic draft checks but have `LSAC@5: not_evaluated`.
- An open source package remains preliminary even if the draft checks pass.
- All actions remain drafts. This iteration has no approval API, dispatch capability, impact calculation, spatial overlay, or numeric lives-saved estimate. It accepts only `not_estimable` abstentions with a reason, which the dashboard shows beside the action.
