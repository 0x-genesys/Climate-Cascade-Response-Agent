# Execution Evidence Ledger

This directory is the append-only operational record for implementation work. The improvement changelog explains whether an iteration helped. Execution entries preserve what was run, what passed or failed, and how to reproduce the finding.

Create one entry before or immediately after each meaningful implementation step. Update it after verification, never by replacing a historical result.

## Required entry fields

- Date and scope
- Sequence number within the date, zero-padded from `01`, so same-day records have an unambiguous order
- ADR step or iteration being implemented
- Assumption and acceptance criteria
- Files changed
- Fixture and configuration versions
- Exact setup, test, and verification commands
- Test and verification output summary
- Failures, deviations, and unresolved risks
- Documentation updates made
- Decision and next step

## Rules

- Write tests before or alongside implementation for every behavior that can fail deterministically.
- Run focused tests first, then the relevant full suite.
- Record a failed command and its cause before retrying with a fix.
- Do not call an iteration complete until its required tests and documentation updates are recorded.
- Link machine-readable outputs, trajectories, screenshots, and fixtures when they exist.
