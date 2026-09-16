# MEMORY.md — daily-log

Dated session log of decisions, patterns, and gotchas. Append-only; never edit past entries.

---

### 2026/09/15 — [this commit] "Write down the daily-log day boundary"

**Duration**:
- 2026/09/15_17:30 - 17:45 (0.3h): added the clock-day rule to the daily-log skill and the matching conformance check to daily-log-audit.

**Summary**: The day boundary was assumed but never stated, so a session running past
midnight had no defined home and could be published as one bullet whose end time preceded
its start. The rule is now explicit: a daily-log day is the clock day in Asia/Taipei,
`00.00` to `23.59`; work crossing midnight is **split at midnight**, the earlier part
staying on the day it started and the remainder becoming the next day's first bullet.
`stm-window.sh`'s `+1d` end marker is named as the signal to split rather than a value to
publish. `daily-log-audit` gained the matching check — an end before its start, a `24.xx`
tick, or a missing after-midnight remainder — so past days get caught and rewritten. The
rule was exercised the same day: a 2026/09/14 session ran to 00:14, and its tail was logged
as 2026/09/15's first bullet.

### 2026/09/08 — "Batch GitHub writes, and pin daily-log composition to Sonnet 5"

**Duration**: 2026/09/08_01:20 - 02:14 (0.9h)

**Summary**: Backfilling 14 missing days meant 14 REST round trips, because the REST API
has no bulk comment endpoint: slow, rate-limit-hungry, and non-atomic, so a failure
halfway leaves the issue half-updated with no record of where it stopped. New
`scripts/gh-batch-comments.sh` puts every create and edit into ONE GraphQL document using
aliased `addComment`/`updateIssueComment` mutations, resolves node ids up front, and
escapes bodies with `json.dumps` (GraphQL and JSON share the escaping rules, and
daily-log bodies are full of quotes, newlines and emoji). `--dry-run` prints the document
before anything is sent. Used it to correct three entries in one request. Also pinned
daily-log composition to Sonnet 5: Claude cannot change its own session model
mid-session, so the rule is stated as delegation to the Sonnet-pinned `project-analyst`
sub-agent with the draft/confirm/post loop kept in the main session — the session returns
to its original model because it never left it. Made mandatory rather than advisory,
since the old wording let a "trivial single-day entry" be composed inline and that
exception never failed to apply. Found that the repo's skill sources had drifted behind
the installed `~/.claude/skills/` copies, so a reinstall would have reverted the model
section; resynced.


### 2026/07/18

- **Tightened the four skill-frontmatter `description` fields** (`daily-log`,
  `daily-log-commit`, `daily-plan`, `daily-log-audit`) — shorter, lead with the trigger
  phrase and explicit alternate trigger wording ("audit / verify / fix my daily log",
  "post my daily log", "plan my day"), dropped restated detail that duplicates the body.
- **`scripts/fetch-auto-daily-log.sh` is now skill-first.** If
  `~/.claude/skills/daily-log-commit/SKILL.md` is installed, the hook prints a 4-line
  pointer at it (Step 1: reconcile/commit/push via the skill using the injected session
  timing; Step 2: run `/daily-log` after the push succeeds) instead of inlining the full
  SOP prompt. The legacy fetch-SOP-or-local-fallback path is kept as the fallback for
  machines without the skill installed.
- **Session-timing gotcha (repeat).** LTM Postgres was unreachable this session (Vault
  AppRole credentials not found in the local keychain), so the exact session start could
  not be recalled. Logged with `??:??` start per the SOP's own missing-start convention;
  end time taken from file mtime (19:13, matches the single day these files were touched).

### 2026/07/08

- **`scripts/fetch-auto-daily-log.sh` now chains a Step 2 reminder after the Step 1
  commit prompt.** Once the injected content (fetched SOP section or the local
  `auto-daily-log.md` fallback) is printed, the hook appends a second block telling the
  agent/user to run `/daily-log` after the push succeeds, so the lab progress-plan
  comment gets posted in the same breath as the commit+push. Fires regardless of
  whether Step 1's content came from GitHub or the offline fallback; the appended block
  self-notes that `/daily-log` no-ops outside the lab orgs, so non-lab repos are
  unaffected.
- **Doc drift fix.** `CONTEXT.md` and `CLAUDE.md` still said "the three daily-log
  skills" / listed only `daily-log`, `daily-log-commit`, `verify-daily-log` in the
  skill-group summary, even though `daily-plan` was added in the prior commit
  (`17b4656`). Updated both to the four-skill roster and reworded the
  `fetch-auto-daily-log.sh` file-map rows to mention the new Step 2 behavior.
  `TODO.md`'s "mention the three skills" README item was similarly reworded to "all
  four skills."

### 2026/06/29

- **MySQL → PostgreSQL LTM migration finished across the docs.** `CLAUDE.md`,
  `.github/copilot-instructions.md`, `lab-automation/global-claude.md`, and
  `lab-automation/global-copilot.md` now describe the per-user PostgreSQL store managed
  by `llm-skill-ltm` (SSH tunnel, `memory` skill in `~/.claude/skills`, SessionStart
  activity hook). All references to the retired `mysql-memory` MCP and the direct
  `140.118.122.119:3306` connection were removed. The session-start recall query is now
  `SELECT … FROM memory WHERE metadata->>'owner' = … AND metadata->>'repo' = …`.
- **`[owner/repo]` bullet tags are now first-class in the markdown contract.** In
  `dailylog_md.py`, `BULLET_RE` gained an optional `(?P<tag>…\[…\])?` group between the
  backticked time and the colon. `patch_daily_logs` preserves an existing tag, else fills
  it from the commit's `repo_full_name`; `append_unmatched_commits` and
  `render_new_day_from_commits` emit the tag too. Pattern: one bullet = one session on one
  project; overlapping time ranges across different tags are allowed (agentic concurrency).
- **`setup-memory.sh` no longer provisions MySQL/MCP.** It now writes prefs + base
  settings only (`~/.claude/CLAUDE.md`, `~/CLAUDE.md` home-tree fallback,
  `~/.copilot/instructions.md`, `~/.claude/settings.json` with the `mysql-memory` MCP entry
  stripped) and delegates the LTM install to `llm-skill-ltm`. Honors `LAB_DEPLOY_SKIP_LTM=1`
  and `LAB_PREFS_FILE` so the new one-touch `deploy-lab-llm.sh` orchestrator can drive it.
- **Gotcha — Claude user-global memory lives at `~/.claude/CLAUDE.md`, not `~/CLAUDE.md`.**
  `setup-memory.sh` writes both: `~/.claude/CLAUDE.md` (cwd-independent, Cowork-safe) plus
  `~/CLAUDE.md` as a home-tree directory-walk fallback.
- **Repo rename `auto-daily-log` → `daily-log` reflected in docs.** CLAUDE.md header +
  layout root updated; this repo is now the home for the daily-log skill group
  (`skills/`, `scripts/`, `install.sh`).
- **Decision — gitignore `.claude/settings.json`.** It is local machine state (held a
  stale absolute path to the old `auto-daily-log` project memory dir), so it joins
  `settings.local.json` in `.gitignore` rather than being committed.
- **Session-timing gotcha.** This transcript only contained today's reconcile session
  (first user message 16:12), but the underlying work was authored 2026/06/24–06/27 per
  file mtimes. Logged the work as a multi-day range accordingly.

### 2026/06/30

- **Synced `scripts/auto-daily-log.md` to the SOP reconcile prompt.** Added the
  "Check the knowledge graph first (graphify)" step so the reconcile syncs the file list
  and architecture from `graphify-out/` before reading files wholesale; kept the per-day
  `work duration` block.
- **Fixed stale `metadata->>'org'` → `metadata->>'owner'`** in the worklog SQL of both the
  `daily-log` and `verify-daily-log` skills. After the owner/repo split the old key matched
  nothing, so the hours query returned empty.
- **Recomposed both skills to the per-`[owner/repo]` task-block format** (`daily-log.md`
  Formatting Standards): one block per repo carrying the 7-digit short-hash commit link as
  evidence, with hour-grouped `HH.MM - HH.MM: <activity>` bullets under it; `??:?? - HH.MM`
  for an unknown start; calendar-meeting-without-minutes placeholder. Added graphify-first
  as step 0 of `daily-log-commit`. Recomputed `.sop-hash` (`b2b3a1bd018495ab`).
