# Daily-log Skill Group

This repo (`bmw-ece-ntust/daily-log`) is the home for the BMW Lab daily-log Claude
skills + the Python tool + the prompt scripts. `install.sh` installs the skills into
`~/.claude/skills`, the scripts into `~/.claude/prompts`, sets `DAILY_LOG_HOME`, and
wires the `UserPromptSubmit` daily-log hook. The `ijosh-ch/claude` preference only
references this repo, it no longer carries these skills.

| Skill | Scope | Trigger | Brief |
| --- | --- | --- | --- |
| `daily-log-commit` | global | `/daily-log-commit` (auto on real `git push`) | Reconcile the 4 project files, commit in SOP `Work Start:` format, push, write an LTM session record. Lab orgs only. |
| `daily-log` | global | `/daily-log` | Post entries to `progress-plan#366` from LTM worklogs + commits (cross-verified). Uses this repo's Python tool (`$DAILY_LOG_HOME`). |
| `verify-daily-log` | global | `/verify-daily-log` | Quickly verify the daily-log vs commits + LTM and fill only missing days. Token-efficient. |

## Layout

```
main.py, src/, reorder-comments.py, fill-from-calendar.py   the Python tool
scripts/   fetch-auto-daily-log.sh (UserPromptSubmit hook), auto-daily-log.md (SOP fallback)
skills/    daily-log, daily-log-commit, verify-daily-log
install.sh wires skills + hook + DAILY_LOG_HOME + tool venv
```

## Dependencies

- `gh` CLI authenticated as your GitHub account.
- For `verify`/`auto`: LTM worklogs from `bmw-ece-ntust/llm-skill-ltm` (installed separately).
- Lab orgs only: `bmw-ece-ntust`, `bmw-ntust-internship`, `raycg`. Issue: `progress-plan#366`.
