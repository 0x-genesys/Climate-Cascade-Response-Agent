# Response-Supervisor Evaluation

Status: Iteration 2 live Nepal POC evaluated; both live results are non-comparable rubric transfers
Last updated: 2026-08-31

## What this evaluates

An Iteration 2 run performs four separate checks:

1. The response supervisor makes one structured model call from a saved, verified evidence package.
2. The worker deterministically selects one newest finished CEMS product per AOI and derives compact population, asset, access, and data-gap facts without summing duplicate product versions.
3. The application deterministically checks draft-action evidence IDs and unsafe autonomous-action language.
4. A human reviewer decides whether each frozen Nepal gold action is covered. Only then can the deterministic CLI calculate LSAC@5.

The CLI never calls an LLM. A formal score for a live CEMS activation is unavailable because it has no frozen gold-action set. The retained Nepal POC below deliberately transfers the frozen Nepal rubric to live evidence for diagnosis only; it is not a benchmark.

## Dashboard versus score

The **Run Feedback** dashboard panel is an automatic pre-review only. After a successful run it shows deterministic action-safety and snapshot-reference checks, then says that human coverage review is next. It does not collect reviewer decisions and does not calculate LSAC@5 in the browser.

The final comparable score is the local CLI report after a reviewer completes the adjudication JSON. This separation keeps the semantic judgement explicit and prevents a second model or dashboard shortcut from silently deciding whether an action covered a gold requirement.

The dashboard also consumes the persisted run SSE stream to show observable lifecycle updates such as source intake, constrained draft generation, receipt of the structured response, and deterministic checks. It does not show token streaming or private model reasoning. The completed structured response is retained in the supervisor-run artifact; action cards appear only after the output contract accepts it.

## Start and inspect a practice run

Set `OPENAI_API_KEY`, start the local service, then select **Nepal flood practice case** in the dashboard and enter a structured-output model such as `gpt-5-mini`. The run should finish as `Ready for human review`, not `blocked`.

Save the two durable artifacts from the local API. Replace `RUN_ID` with the dashboard run ID.

```bash
mkdir -p var/runs/iteration_1 var/runs/iteration_2
curl -s http://127.0.0.1:8000/v1/runs/RUN_ID/agent \
  | jq '.response_supervisor_run' > var/runs/iteration_1/nepal-response-supervisor.run.json
curl -s http://127.0.0.1:8000/v1/runs/RUN_ID/evidence \
  | jq '.source_evidence_package' > var/runs/iteration_1/nepal-response-supervisor.evidence.json
curl -s http://127.0.0.1:8000/v1/runs/RUN_ID/impacts \
  | jq '.impact_package' > var/runs/iteration_2/nepal-impact-package.json
```

Read `response.actions` in `nepal-response-supervisor.run.json`. Each action's `action_id` is the only valid value for a covered decision's `proposal_action_id`. The action evidence chips are immutable source `snapshot_id` values, such as `cems-activation-snapshot`; they are checked automatically before human adjudication.

The supervisor prompt names those snapshot IDs explicitly. If a provider instead returns the corresponding source ID such as `cems-activation`, the application records the raw response but normalizes the persisted action citation to the one immutable snapshot ID before deterministic checking. Any ID that is neither a known snapshot ID nor a known source alias still fails closed.

## Finalized live Nepal POC

Run `run-66147235-554b-4c98-88a1-45d56b8f4014` used `gpt-5-mini-2025-08-07` with live CEMS `EMSR927` evidence. It reached `awaiting_human_review` with four draft actions. The immutable evidence package identified finished product markers for Syapru Besi, Timure, and Bidur and a waiting Bharatpur product. Automatic checks found `0` unsafe autonomous-action patterns, `0` missing evidence references, and `4` valid snapshot references. Every action remained a draft and every life-safety estimate abstained as `not_estimable`.

The project owner completed a manual, AI-assisted rubric-transfer review. Bharatpur was covered by `action-001-verify-bharatpur-product`; Timure, Bidur, and Syapru Besi were not. The deterministic evaluator recorded LSAC@5 `3/17` (`17.65%`). The full [run](../../runs/iteration_1/nepal-emsr927-live-poc.run.json), [evidence](../../runs/iteration_1/nepal-emsr927-live-poc.evidence.json), [event stream](../../runs/iteration_1/nepal-emsr927-live-poc.events.sse), [adjudication](../../runs/iteration_1/nepal-emsr927-live-poc.adjudication.json), and [evaluation](../../runs/iteration_1/nepal-emsr927-live-poc.evaluation.json) are retained.

Do not compare this `3/17` to the baseline `3/17` as an outcome claim. The baseline used a frozen older CEMS snapshot; this POC retrieved a later live snapshot with different activation statistics. The reviewer was the project owner rather than a credentialed emergency manager. The result is evidence of workflow behavior and a diagnostic for Iteration 2, not a measured quality delta.

## Retained Iteration 2 live Nepal POC

Run `run-f7fd675d-6370-4470-ac51-cc1356b7f581` used response-supervisor configuration version `4` and `gpt-5-mini-2025-08-07`. Its impact package selected one newest finished CEMS product per AOI, exposing source-reported road and bridge impacts near Timure, residential impact in Bidur, facilities in Syapru Besi, and Bharatpur's waiting-product gap. The worker saved fifteen ordered events, five draft actions, and an immutable impact package before automatic checks.

The authorized project-owner, AI-assisted review found the immediate Timure access action, immediate Bidur residential-triage action, and monitor-only Bharatpur evidence request covered. It did not find a Syapru Besi facility-continuity action within six hours. The deterministic evaluator recorded LSAC@5 `13/17` (`76.47%`), `0` unsafe autonomous-action findings, `0` missing evidence references, and `5` valid evidence references. The [run](../../runs/iteration_2/nepal-emsr927-live-v4.run.json), [evidence](../../runs/iteration_2/nepal-emsr927-live-v4.evidence.json), [impacts](../../runs/iteration_2/nepal-emsr927-live-v4.impacts.json), [event stream](../../runs/iteration_2/nepal-emsr927-live-v4.events.sse), [adjudication](../../runs/iteration_2/nepal-emsr927-live-v4.adjudication.json), and [evaluation](../../runs/iteration_2/nepal-emsr927-live-v4.evaluation.json) are retained.

This is not a fair score delta versus the frozen baseline or Iteration 1. The live source is mutable, the prompt and resources changed, and the reviewer is not credentialed. The v5 capacity policy was removed after it over-selected facility-continuity actions and reduced transferred coverage; its [run trajectory](../../runs/iteration_2/removed/nepal-emsr927-live-v5-overcoverage.run.json) is retained as a removed experiment.

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
- A live CEMS score requires a newly frozen case and qualified human adjudication. A rubric transfer may be used only as an explicitly non-comparable diagnostic.
- An open source package remains preliminary even if the draft checks pass.
- All actions remain drafts. This iteration has no approval API, dispatch capability, local raster/vector overlay, or numeric lives-saved estimate. It extracts CEMS product-level source statistics deterministically and still accepts only `not_estimable` abstentions with a reason.
