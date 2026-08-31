# Iteration 1 Response-Supervisor Evaluation

Status: Implemented; no credentialed agent run has been human-adjudicated yet
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
