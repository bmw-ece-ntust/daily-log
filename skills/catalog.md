# Daily-log Skill Group

This repo (`bmw-ece-ntust/daily-log`) is the home for the BMW Lab daily-log Claude
skills + the Python tool + the prompt scripts. `install.sh` installs the skills into
`~/.claude/skills`, the scripts into `~/.claude/prompts`, sets `DAILY_LOG_HOME`, and
wires the `UserPromptSubmit` daily-log hook. The `ijosh-ch/claude` preference only
references this repo, it no longer carries these skills.

| Skill | Scope | Trigger | Brief |
| --- | --- | --- | --- |
| `daily-plan` | global | `/daily-plan` | Post the morning plan for today to `progress-plan#366`: a checklist of measurable targets (time ticks optional — none / `hh:mm` deadline / `hh:mm - hh:mm` duration). The evening log fills the same comment. |
| `daily-log-commit` | global | `/daily-log-commit` (auto on real `git push`) | Reconcile the 4 project files, commit in SOP `work duration:` format, push, write an LTM session record. Lab orgs only. |
| `daily-log` | global | `/daily-log` | Sweep all lab repos with the `daily-log-commit` workflow (commit + push pending work), then post entries to `progress-plan#366` from LTM worklogs + commits (cross-verified) — updating the day's existing plan/log comment in place, creating one only if none exists. Uses this repo's Python tool (`$DAILY_LOG_HOME`). |
| `daily-log-audit` | global | `/daily-log-audit` | Full-history audit: recheck every day against the current SOP format, rewrite non-conforming entries, fill missing days (supersedes `verify-daily-log`; pass `--since <date>` for the old quick gap-check scope). Token-efficient. |

## Layout

```
main.py, src/, reorder-comments.py, fill-from-calendar.py   the Python tool
scripts/   fetch-auto-daily-log.sh (UserPromptSubmit hook), auto-daily-log.md (SOP fallback)
skills/    daily-plan, daily-log, daily-log-commit, daily-log-audit
install.sh wires skills + hook + DAILY_LOG_HOME + tool venv
```

## Dependencies

- `gh` CLI authenticated as your GitHub account.
- For `audit`/`auto`: LTM worklogs from `bmw-ece-ntust/llm-skill-ltm` (installed separately).
- Lab orgs only: `bmw-ece-ntust`, `bmw-ntust-internship`, `raycg`. Issue: `progress-plan#366`.
