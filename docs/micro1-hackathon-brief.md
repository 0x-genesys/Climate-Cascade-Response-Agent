# Micro1 Agentic Workflows Hackathon Brief

Status: Maintained text reference
Source: [original PDF](micro1%20-%20First%20Hackathon97ce7c5.pdf)
Last transcribed: 2026-08-30

This Markdown file preserves the practical guidance from the supplied Micro1 hackathon PDF so that repository skills and project documents can reference it without re-extracting the PDF. It is a normalized text transcription, not a replacement for the original visual document.

## Welcome and challenge

Choose a specific, meaningful problem that people would genuinely find useful. Explain who has the problem, the bottleneck they face, why it matters in practice, whether the agent solves it well, and whether another person can reproduce the result.

The goal is to demonstrate through clear evidence that the solution improves how the task is handled today.

## Purposeful agent design

Use the capabilities that fit the problem. Better context, tools, memory, verification, specialized skills, and multi-agent orchestration are possible choices, but judges value purposeful choices over component count. Each design choice should improve reliability or help the agent reach the goal.

## Baseline and improvement

Start with a simple, reasonable baseline. Examples include one direct prompt, one general-purpose agent with basic tools, a simple script or template, or the manual process used today.

Give the baseline and final solution the same task and evaluation cases. Explain meaningful resource differences. Use the final comparison to show the overall improvement, and use the changelog to explain where the improvement came from.

## Improvement changelog

Record every meaningful experiment, including removed experiments. For each entry, state what was tried, why it was tried, the evidence produced with the same evaluation method where practical, and the resulting decision or learning.

Suggested progression:

| Stage | What to record |
| --- | --- |
| Baseline | Basic approach, initial result, and established starting point. |
| Iteration 1 | A change such as a skill, the observed issue it targets, the new result, and whether it was kept, revised, or removed. |
| Iteration 2 | A verification change after an observed failure, its result, and decision. |
| Iteration 3 | An orchestration or design change, its result, and decision. |
| Final | The retained changes, final result, and main contribution. |

## Evaluation

Choose one primary metric that reflects success for the intended user. Define what a good final result looks like before running the evaluation. Use the same cases for baseline and final solution. Ten or more cases are a good target when the task permits, and include one challenging case with an explanation of what it revealed.

Also report supporting measures that matter to the user, such as human time per task and cost per task. If a standard format does not fit the task, define a clear scoring rubric for judges to use.

Suggested table:

| Metric | Simple baseline | Agent solution | Change |
| --- | --- | --- | --- |
| Primary outcome | value | value | delta |
| Human time per task | value | value | delta |
| Cost per task | value | value | delta |

## Judging rubric

Projects are scored out of 100 points.

| Criterion | Points | Strong work |
| --- | ---: | --- |
| Problem and User Value | 15 | Solves a meaningful problem for a clearly defined user and explains the bottleneck and practical value. |
| Agent Solution and Engineering | 30 | Uses agents purposefully with technically sound context, tools, memory, verification, skills, or orchestration choices. |
| End-to-End Quality | 20 | Completes a realistic, self-contained workflow with a final result that the intended user could use and sign their name to. |
| Measured Improvement | 15 | Demonstrates a fair gain over the baseline and connects each meaningful iteration to evidence. |
| Reproducibility | 15 | Gives another person a clear clean-environment path to run baseline and solution and reproduce the main result. |
| Hot Take and Insights | 5 | Turns an observed failure mode into a practical lesson for more reliable agents. |

## Ground rules

1. Use tools and components you already know if they are appropriate.
2. Clearly identify what existed before the competition and what was added during it.
3. Follow all component licenses and service terms.
4. Keep consequential actions in a sandbox or simulation and require human approval before action.
5. Include a qualified human reviewer for work that could significantly affect someone.
6. Choose a legal and ethical use case and treat people and data responsibly.
7. Use shareable information. Public, synthetic, or approved anonymized data are preferred.
8. Keep credentials and private information outside the submission.
9. Connect result claims to submitted evidence.
10. Give judges enough access to run the project and reproduce the main result.

## Required deliverables

### Complete solution code and improvement changelog

Share the full project and everything required to run it, including agent instructions. The README should introduce the intended user, current bottleneck, and practical value. Include a clearly labeled improvement changelog with an entry for each meaningful iteration, evidence guiding the next decision, the main failure mode, and the final insight.

### Reproduction guide

Write for a clean environment. Provide setup plus exact commands for baseline, solution, and evaluation. Explain required data, expected output, relevant versions, approximate runtime, and cost.

### Solution video

Keep the video to five minutes or less. Start with the problem and simple baseline, show one realistic execution from start to finish, show the final comparison, briefly explain the changelog, and highlight the largest retained improvement plus one removed experiment.

### Agent trajectories

Include representative trajectories for every agent. Show instructions, agent actions, tool responses, feedback, retries, and human checkpoints in a form that is easy to follow through to the final result.

## Appendix examples

The PDF gives three reference problem shapes:

- **Repository-quality analysis:** a buyer needs a repeatable assessment of an unfamiliar codebase. Evaluate the agent and baseline against a qualified reviewer ranking of fixed approved repositories.
- **Candidate evaluation:** recruiters need to reconcile a job description, target profile, CV, interview records, and assessments without treating suspicion as proof. Use approved or synthetic cases, include a conflicting-evidence case, and retain human decision authority.
- **Podcast translation:** creators need translated episodes to preserve speaker identity, recurring terminology, tone, and earlier translation choices. Evaluate a fixed set of episodes and languages, include a recurring-detail case, and trace choices to source audio or approved material.

Across all examples, define the evaluation before running it, pin the cases, preserve evidence, report failures, and let another reviewer reproduce the result from the same materials.
