# CLAUDE.md — daily-log

Static knowledge snapshot for LLMs. Describes repo layout, conventions, and key behaviours.

---

## Purpose

Automated daily-log tool for BMW Lab students at NTUST. Posts one GitHub issue comment per working day to a designated progress-plan issue, seeded from:
- Git commit history across configured organisations / repos
- Google Calendar events (optional)
- Planning sources (issue body, local markdown files)

Spec: [SOP daily-log.md § Auto Daily-log](https://github.com/bmw-ece-ntust/SOP/blob/master/daily-log.md#auto-daily-log)

This repo (`bmw-ece-ntust/daily-log`, formerly `auto-daily-log`) is also the **home for the Claude daily-log skill group**. `install.sh` copies `skills/` into `~/.claude/skills`, `scripts/` into `~/.claude/prompts`, sets `DAILY_LOG_HOME`, and wires the `UserPromptSubmit` daily-log hook. The `ijosh-ch/claude` preference repo no longer carries these skills — it only points here.

---

## Skills

| Skill | Trigger | Brief |
|---|---|---|
| `daily-plan` | `/daily-plan` | Post the morning plan for today to `progress-plan#366`: a checklist of measurable targets, time ticks optional (none / `hh:mm` deadline / `hh:mm - hh:mm` duration). The evening `/daily-log` fills the same comment in place. |
| `daily-log-commit` | `/daily-log-commit` (auto on a real `git push`) | Reconcile the 4 project files, commit in SOP `work duration:` format, push, write an LTM session record. Lab orgs only. |
| `daily-log` | `/daily-log` | Commit + push all lab repos with pending work (`daily-log-commit` sweep), then post entries to `progress-plan#366` from LTM worklogs + commits (cross-verified) — updating the day's existing plan/log comment in place, creating one only if none exists. |
| `daily-log-audit` | `/daily-log-audit` | Full-history audit vs the current SOP format: rewrite non-conforming entries in place and fill missing days (supersedes `verify-daily-log`; `--since <date>` = old quick gap-check). |

---

## Repository Layout

```
daily-log/
├── main.py                        # Entrypoint: adds src/ to path, auto-loads env.yaml
├── install.sh                     # Installs skills → ~/.claude/skills, prompts → ~/.claude/prompts, sets DAILY_LOG_HOME, wires the UserPromptSubmit daily-log hook, builds the venv
├── env.example.yaml               # Config template — copy to env.yaml (safe to commit)
├── env.local.example.yaml         # Template for gitignored private overrides → env.local.yaml
├── reorder-comments.py            # Standalone: gap analysis + chronological reorder of issue comments
├── fill-from-calendar.py          # Standalone: fill missing entries from ICS/iCal feed or OAuth
├── enable_nemotron_copilot.py     # Standalone: register the remote vLLM Nemotron model as a custom OpenAI-compatible model in VS Code Copilot Chat
├── requirements.txt               # Runtime deps: PyYAML; optional Google Calendar libs
├── README.md                      # Usage guide and Quick Claude Prompts for common tasks
├── CLAUDE.md                      # Static knowledge snapshot for LLMs (this file)
├── .sop-hash                      # SHA-256[:16] of the SOP ## Auto Daily-log section
├── .claude/
│   └── settings.local.json        # Project-local Claude Code permissions (gitignored; settings.json is local too)
├── .github/
│   ├── copilot-instructions.md    # Per-repo Copilot context (project purpose, conventions)
│   └── workflows/
│       └── sop-check.yml          # Midnight weekday check against SOP (needs SOP_READ_TOKEN secret)
├── skills/                        # Claude daily-log skill group (installed by install.sh)
│   ├── catalog.md                 # Index of the skill group; explains install + hook wiring
│   ├── daily-plan/SKILL.md        # /daily-plan — post the morning target checklist for today (times optional)
│   ├── daily-log/SKILL.md         # /daily-log — post entries to progress-plan#366 (the posting step)
│   ├── daily-log-commit/SKILL.md  # /daily-log-commit — reconcile 4 files, commit (SOP work duration format), push, write LTM record
│   └── daily-log-audit/SKILL.md   # /daily-log-audit — full-history audit vs SOP format, rewrite non-conforming entries, fill gaps
├── scripts/                       # Prompt + hook scripts (installed into ~/.claude/prompts)
│   ├── auto-daily-log.md          # Canonical daily-log-commit prompt (fallback when GitHub unreachable)
│   └── fetch-auto-daily-log.sh    # UserPromptSubmit hook: detect git push/commit, resolve session log, inject the Step 1 prompt, append Step 2 (/daily-log) reminder
├── lab-automation/
│   ├── deploy-lab-llm.sh          # ONE-TOUCH: clone/update llm-core + llm-skill-ltm + daily-log, install prefs + all skills + LTM + hooks, optional --backfill, DB self-check
│   ├── setup-memory.sh            # Prefs + base settings: writes ~/.claude/CLAUDE.md + ~/.copilot/instructions.md + ~/.claude/settings.json, then runs the LTM install (skipped when LAB_DEPLOY_SKIP_LTM=1)
│   ├── global-claude.md           # Source for ~/.claude/CLAUDE.md (global AI prefs, mirrored from bmw-ece-ntust/llm-core)
│   └── global-copilot.md          # Source for ~/.copilot/instructions.md (global Copilot instructions)
└── src/dailylog/
    ├── cli.py                     # Argument parser and main orchestration
    ├── config.py                  # YAML → frozen dataclasses (AppConfig and sub-configs)
    ├── github_api.py              # GitHub commit search + issue comment CRUD via gh CLI (utf-8 safe)
    ├── dailylog_md.py             # Markdown parse/patch: bullet regex, time-range update, commit linking
    ├── gcal.py                    # Google Calendar OAuth2 integration
    ├── planning.py                # Suggestion ranking from issue body or local markdown files
    ├── overleaf.py                # Overleaf local-git integration (summarise by day)
    ├── llm.py                     # Optional OpenAI-compatible LLM provider
    ├── reminder.py                # Generate reminder.md (missing dates + no-evidence activities)
    ├── restore.py                 # Restore daily-log comments from a JSON backup
    ├── __init__.py
    └── __main__.py                # python -m dailylog entrypoint
```

---

## Config

### `env.yaml` (committed, no secrets)

Copy `env.example.yaml` → `env.yaml`.

| Field | Purpose |
|---|---|
| `github.login` | Your GitHub username (used to attribute commits) |
| `github.contribution_sources.orgs` | Orgs to scan for your commits |
| `github.contribution_sources.repo_owners` | Additional users whose repos to include |
| `github.contribution_sources.repos` | Specific `owner/repo` entries |
| `github.repo_owner / repo_name / issue_number` | Target issue for daily-log comments |
| `github.seed_new_day_from_commits` | Auto-seed new day bullets from commits |
| `github.append_unmatched_commits` | Append unreferenced commits as new bullets |
| `timeline.lookback_days` | Default window for missing-date checks |
| `timeline.start_date` | Historical start for full backfill |
| `google_calendar.*` | Optional OAuth2 calendar integration |
| `planning.*` | Optional task suggestion seeding |
| `overleaf.*` | Optional Overleaf local-git summary |
| `llm.*` | Optional OpenAI-compatible LLM analysis |

### `env.local.yaml` (gitignored, secrets)

Copy `env.local.example.yaml` → `env.local.yaml`. Used by `fill-from-calendar.py`.

| Field | Purpose |
| --- | --- |
| `google_calendar.ical_url` | Private iCal URL (Google Calendar → Settings → "Secret address in iCal format") |
| `google_calendar.calendar_id` | Calendar ID for OAuth path (e.g. `user@gapps.ntust.edu.tw`) |
| `google_calendar.exclude_keywords` | Substrings that mark an event as personal (case-insensitive); matched events are skipped |

---

## Daily-Log Comment Format

```markdown
### YYYY/MM/DD

**Short-term Goal**:
<one-line goal>

**Daily-logs**:
- `HH.MM - HH.MM` [owner/repo]: [description](https://github.com/org/repo/blob/abc1234/path/file.md#section)
- `HH.MM - ` [owner/repo]: <ongoing activity>
```

Rules:
- Date heading: `### YYYY/MM/DD` (Asia/Taipei timezone)
- Time ticks use **dot notation**: `HH.MM` (not colons)
- One bullet = one session on one project. Tag each bullet with its `[owner/repo]` project (owner = the GitHub account, org or personal; repo = name only). The tool fills this from the commit's `repo_full_name`.
- Tasks may overlap in time (agentic AI runs tasks concurrently); overlapping ranges across different `[owner/repo]` tags are allowed.
- Evidence link must point to a **specific file blob URL** with 7-char commit hash + anchor
- Special time-tick values: `` `SICK LEAVE` ``, `` `HOLIDAY` ``, `` `ABSENT` ``

> **Note:** The SOP example uses `HH:MM` colon notation. This tool normalises to `HH.MM` dots.
> The `.sop-hash` workflow will alert if the SOP section changes.

---

## Authentication

| Service | Method |
| --- | --- |
| GitHub | `gh auth login` — no tokens in files |
| Google Calendar (OAuth2) | `credentials.json` from Google Cloud Console, cached `token.json`; browser redirect via `InstalledAppFlow.run_local_server` |
| Google Calendar (iCal) | Private iCal URL in `env.local.yaml` — no OAuth needed; acts as a bearer token in the URL |

---

## Key Behaviours

### Markdown parsing (`dailylog_md.py`)

- `parse_heading_date` — extracts `YYYY/MM/DD` from `### YYYY/MM/DD` heading (also handles blockquoted and fallback bubble-header form)
- `patch_daily_logs` — matches bullet activities to commits by title similarity, fills end time and adds evidence link
- `append_unmatched_commits` — adds commits not yet referenced anywhere in the comment
- `patch_short_term_goal` — replaces content under `**Short-term Goal**:` with provided lines
- `render_new_day_*` — templates for seeding a brand-new day comment

### Commit search (`github_api.py`)

- Uses `gh api search/commits` with `committer-date` range (±1 day buffer)
- Bucketed by Asia/Taipei timezone
- Deduplicates across multiple query sources
- `enrich_commits_with_file_urls` — optional, resolves each commit to its primary `.md` file (one extra API call per commit)

### CLI orchestration (`cli.py`)

Order of operations per run:
1. Fetch all existing daily-log comments for the date range
2. Optionally fetch Google Calendar events
3. Fetch commits from all configured sources
4. `--ensure-comments` → create missing day comments (seeded from commits or plans)
   - `--skip-if-no-activity` — skip creating a stub when no commits exist for that day
5. Patch existing comments: fill end times, add evidence links, append unmatched commits
6. `--include-overleaf` → append Overleaf summary
7. `--generate-reminder` → write reminder.md

### Gap analysis and reorder (`reorder-comments.py`)

Standalone script — does not use `env.yaml`.

- Fetches all comments from the configured issue via `gh issue view --json comments`
- Separates dated entries (matching `### YYYY/MM/DD`) from undated/administrative ones
- Reports missing weekdays in a configurable `--since` / `--until` window
- Reports out-of-order dated entries
- `--apply` — deletes all dated comments and recreates them in sorted order (destructive; dry-run by default)
- `--gcal` — cross-checks missing days against Google Calendar (uses `gcal.py` OAuth flow)

### Calendar-seeded backfill (`fill-from-calendar.py`)

Standalone script — reads private config from `env.local.yaml`.

- Source priority: CLI argument (file path or URL) → `ical_url` from `env.local.yaml` → `--oauth` flag
- Parses ICS bytes via the `icalendar` library; converts all datetimes to Asia/Taipei
- Deduplicates recurring meeting invites on `(start, end, summary)` tuple
- Filters personal events via `google_calendar.exclude_keywords` from `env.local.yaml`
- Reports missing weekdays that have calendar events, formatted as ready-to-paste daily-log bullets (`HH.MM` dot notation)
- `--create` — posts a new daily-log comment for each missing day with events
- `--all` — also audits days that already have a log entry (for cross-referencing)

---

## SOP Sync Workflow (`.github/workflows/sop-check.yml`)

Runs every weekday at midnight Taiwan time (16:00 UTC). Requires a repository secret:

| Secret | Value |
|---|---|
| `SOP_READ_TOKEN` | Fine-grained PAT with **Contents: Read-only** on `bmw-ece-ntust/SOP` |

If the `## Auto Daily-log` section hash changes from `.sop-hash`, the workflow opens a GitHub issue labelled `sop-sync`. To acknowledge a change: review the SOP diff, update README/implementation, then update `.sop-hash` and commit.

---

## Long-Term Memory (per-user Postgres)

The lab LTM is the per-user Postgres store managed by the **`llm-skill-ltm`** repo (one DB per member on the lab box, reached over an SSH tunnel; attribution is by GitHub account). It supersedes the old `mysql-memory` MCP. It works the same in Claude Code and Cowork because the `memory` skill is installed into `~/.claude/skills` by `llm-skill-ltm/install.sh`, which also wires the SessionStart activity hook.

What it stores (no raw prompts/responses):
- `activity` — one row per repo per day (SessionStart hook + `memory-backfill.sh`).
- `worklog` — one row per session with **exact start/end timestamps** (`stm-backup.sh`); use these for daily-log start times.
- Each row's `metadata` keeps `owner` (the GitHub account, org or personal) and `repo` (name only) as **separate fields**, so activities group per project for the daily-log.

**Session start** — recall recent work for a project via the `memory` skill (recall-by-repo):
```sql
SELECT metadata->>'date', metadata->>'machine', metadata->>'branch', type, description
FROM memory
WHERE metadata->>'owner' = :'owner' AND metadata->>'repo' = :'repo'
ORDER BY metadata->>'date' DESC;
```

**Feeding the daily-log** — combine commit history with the matching `worklog` rows to get each session's start/end time, then emit one bullet per session tagged with `[owner/repo]`.

Setup / bootstrap a machine: see `llm-skill-ltm` (`setup.sh` → `install.sh`).

---

## Conventions

- Always run `--dry-run` first; switch to `--apply` only after confirming output
- Skip weekends when backfilling — run Mon–Fri ranges only
- Asia/Taipei (GMT+8) is the single authoritative timezone throughout
- Evidence links must be file-specific with a 7-char commit hash anchor (not branch-head links)
