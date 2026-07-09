# CONTEXT.md — daily-log

Architecture overview and environment map for the BMW Lab daily-log tool + skill group.
Companion to `CLAUDE.md` (static repo snapshot); this file captures how the pieces fit
together and which external services they touch.

---

## What this repo is

Three things in one repo (`bmw-ece-ntust/daily-log`, formerly `auto-daily-log`):

1. **Python tool** (`src/dailylog/`, driven by `main.py`) — searches GitHub commit
   history, optionally Google Calendar, and posts/patches one daily-log comment per
   working day on `bmw-ece-ntust/progress-plan#366`.
2. **Claude skill group** (`skills/`) — `daily-log`, `daily-log-commit`, `daily-plan`,
   `daily-log-audit`, installed into `~/.claude/skills` by `install.sh`.
3. **Lab automation** (`lab-automation/`) — bootstrap scripts that install global AI
   prefs and the PostgreSQL long-term memory across lab machines.

## Architecture overview

```
commits (gh api) ─┐
gcal events ──────┤→ cli.py orchestration → dailylog_md.py (parse/patch markdown)
LTM worklogs ─────┘                                │
                                                   ▼
                                  github_api.py → progress-plan#366 comment
```

- **`cli.py`** is the orchestrator: fetch existing comments → fetch commits (+gcal) →
  ensure missing-day comments → patch existing (end times, evidence links, unmatched
  commits) → optional Overleaf/reminder.
- **`dailylog_md.py`** owns the markdown contract: `BULLET_RE` now parses an optional
  `[owner/repo]` project tag between the backticked time range and the colon; patch /
  append / render helpers preserve or fill that tag from each commit's `repo_full_name`.
- **`github_api.py`** wraps the `gh` CLI (commit search + issue-comment CRUD, utf-8 safe).
- **`gcal.py` / `planning.py` / `overleaf.py` / `llm.py`** are optional enrichment sources.

## Key files map

| Path | Role |
|---|---|
| `main.py` | Entrypoint; adds `src/` to path, auto-loads `env.yaml` |
| `install.sh` | Installs skills + prompts, sets `DAILY_LOG_HOME`, wires the daily-log hook, builds venv |
| `src/dailylog/cli.py` | Argument parser + per-run orchestration |
| `src/dailylog/dailylog_md.py` | Bullet regex, time-range update, `[owner/repo]` tagging, commit linking |
| `src/dailylog/github_api.py` | GitHub commit search + comment CRUD via `gh` |
| `src/dailylog/config.py` | YAML → frozen dataclasses |
| `skills/*/SKILL.md` | The four daily-log skills |
| `scripts/auto-daily-log.md` | Canonical commit-prompt (also the hook's offline fallback) |
| `scripts/fetch-auto-daily-log.sh` | UserPromptSubmit hook — detects git push/commit, injects the Step 1 commit prompt, then appends a Step 2 reminder to run `/daily-log` after the push succeeds |
| `lab-automation/deploy-lab-llm.sh` | One-touch deploy of llm-core + llm-skill-ltm + daily-log |
| `lab-automation/setup-memory.sh` | Writes global prefs + base settings, delegates LTM install to llm-skill-ltm |
| `enable_nemotron_copilot.py` | Registers the local vLLM Nemotron model in VS Code Copilot Chat |

## External services & environment

- **GitHub** — auth via `gh auth login` (no tokens in files). Target issue
  `bmw-ece-ntust/progress-plan#366`. Eligible orgs for skills: `bmw-ece-ntust`,
  `bmw-ntust-internship`, `raycg`.
- **Long-term memory** — **per-user PostgreSQL** on the BMW Lab box, reached over an
  SSH tunnel, managed by [`llm-skill-ltm`](https://github.com/bmw-ece-ntust/llm-skill-ltm).
  Replaces the retired `mysql-memory` MCP (`140.118.122.119:3306`). The `memory` skill
  recalls/stores rows; a SessionStart hook writes `activity` (per repo/day) and
  `stm-backup.sh` writes `worklog` (exact start/end timestamps). `metadata` keeps
  `owner` and `repo` as separate fields.
- **Google Calendar** — optional; OAuth2 (`credentials.json` + cached `token.json`) or a
  private iCal URL in `env.local.yaml`.
- **vLLM Nemotron** — optional local model host (`enable_nemotron_copilot.py` registers it
  in VS Code Copilot at a Tailscale IP).
- **Timezone** — Asia/Taipei (GMT+8) is authoritative everywhere.

## Config files

- `env.yaml` (committed, no secrets) — copy of `env.example.yaml`.
- `env.local.yaml` (gitignored, secrets) — copy of `env.local.example.yaml`; iCal URL etc.
- `.claude/settings.json` and `.claude/settings.local.json` — local machine state, both gitignored.
