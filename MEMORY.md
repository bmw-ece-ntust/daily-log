# MEMORY.md — daily-log

Dated session log of decisions, patterns, and gotchas. Append-only; never edit past entries.

---

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
