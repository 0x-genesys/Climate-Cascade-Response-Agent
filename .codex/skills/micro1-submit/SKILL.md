---
name: micro1-submit
description: "Assemble and harden a Micro1 hackathon submission package with code, changelog, reproduction guide, video checklist, and agent trajectories aligned to the published rubric."
---

# Micro1 Submit

Use this skill when preparing the final submission package or checking whether the current workspace is ready to submit.

Read [references/hackathon-brief.md](references/hackathon-brief.md) before final packaging.

## Submission goal

Produce a package that passes qualification and makes scoring easy for the judges.

The final package must make four things obvious:

- what the baseline is
- what changed in the improved solution
- how to reproduce both
- why the improved version is meaningfully better

## Required artifacts

Ensure the workspace contains or can generate:

- complete solution code
- improvement changelog
- reproduction guide
- solution video plan or checklist
- representative agent trajectories

## Packaging standards

- Write setup instructions for a clean environment.
- Include exact commands for install, baseline run, improved run, and evaluation.
- State required data, environment variables, versions, expected outputs, runtime, and approximate cost when relevant.
- Keep claims tied to evidence. If a statement cannot be backed by a reproducible artifact, weaken or remove it.
- Make the changelog chronological and decision-oriented, not a generic feature list.

## Final review checklist

- qualification risk: can a judge run this without guessing
- comparison clarity: is the baseline distinct from the improved path
- evidence quality: are the claimed improvements actually visible
- reproducibility: are commands, inputs, and outputs documented
- trajectory quality: do the traces show prompts, tool use, feedback, retries, and checkpoints
- insight quality: is there a credible hot take or failure-mode lesson

## Video guidance

Keep the video focused on:

1. the problem
2. the baseline
3. one realistic end-to-end run
4. the measured comparison
5. the single most important change
6. one discarded experiment

## Preferred behavior

If the package is incomplete, close the highest-risk gaps first: reproducibility, missing evidence, missing trajectories, then polish.
