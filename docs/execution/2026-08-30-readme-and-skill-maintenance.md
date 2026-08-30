# Execution Record: README and Skill Maintenance

Date: 2026-08-30
Scope: Micro1 README entry point, maintained hackathon text reference, project-skill documentation rule, and removal of the local no-mistakes gate instructions.

## Changes

- Added a root README that defines the emergency-operations user, bottleneck, flood and debris-flow MVP boundary, Nepal fixture status, baseline test path, live baseline command, OpenAI environment-variable setup, expected artifacts, and submission evidence links.
- Added `docs/micro1-hackathon-brief.md`, a maintained Markdown transcription of the supplied Micro1 PDF.
- Added project-skill rules requiring README updates when setup, data, commands, configuration, benchmark status, or reproduction expectations change.
- Removed the root no-mistakes workflow rule and deleted its installed root skill after the user requested that the project no longer use it.

## Verification

The README commands were checked against the current `pyproject.toml`, CLI argument contract, `.env.example`, fixture path, and baseline evaluation guide. The README intentionally states that `.env` is not automatically loaded, preventing a secret-setup instruction that the current CLI would silently ignore.

```bash
uv sync --group dev
uv run pytest
uv run climate-cascade-baseline --help
uv run --with pyyaml python /Users/karanahuja/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/climate-cascade-response
uv run --with pyyaml python /Users/karanahuja/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/micro1-build
```

Result: dependency synchronization succeeded; `19 passed in 0.16s`; CLI help exposes every README argument; both project skills validated successfully. The temporary PyYAML dependency was used only for the skill validator and did not change project dependencies.

## Finding

The README is an entry point, not a replacement for evaluation evidence. It links measured artifacts and clearly marks live model quality and LSAC@5 as unmeasured until a credentialed run with human coverage adjudication exists.
