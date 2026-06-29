# Copilot Instructions — auto-daily-log

## Project

Automated daily-log tool for BMW Lab students at NTUST. Posts GitHub issue comments to bmw-ece-ntust/progress-plan#366, seeded from commits and Google Calendar. See `CLAUDE.md` for full layout.

## Long-Term Memory (PostgreSQL)

See global instructions in `~/.copilot/instructions.md`. The lab LTM is a per-user PostgreSQL store managed by the [`llm-skill-ltm`](https://github.com/bmw-ece-ntust/llm-skill-ltm) repo (replaces the old MySQL setup); the `memory` skill in `~/.claude/skills` records and recalls it.

**When working on this repo**, activity is recorded automatically with `owner` = `bmw-ece-ntust` and `repo` = `auto-daily-log` as separate `metadata` fields.

## Conventions

- Time notation: `HH.MM` (dots, not colons) in daily-log bullets
- Timezone: Asia/Taipei (GMT+8) for all date/time bucketing
- Evidence links: file blob URL with 7-char commit hash + section anchor
- Always `--dry-run` before `--apply`
- Config: `env.yaml` (copy from `env.example.yaml`, never commit secrets)
