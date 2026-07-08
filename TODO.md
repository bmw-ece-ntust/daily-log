# TODO.md — daily-log

Prioritized task list. `[x]` = done, `[ ]` = open.

---

## Now

- [ ] Verify `deploy-lab-llm.sh` end-to-end on a clean macOS machine (clone → prefs → LTM → daily-log install → optional `--backfill`).
- [ ] Confirm `install.sh` wires the `UserPromptSubmit` daily-log hook correctly when `~/.claude/settings.json` already exists (jq merge path).

## Next

- [ ] Backfill `[owner/repo]` tags on existing `progress-plan#366` comments that predate the tag format.
- [ ] Update `README.md` Quick Claude Prompts to mention all four skills (`/daily-log`, `/daily-log-commit`, `/daily-plan`, `/verify-daily-log`).
- [x] Re-check `.sop-hash` against the current SOP `## Auto Daily-log` section after the format changes (tags + `HH.MM`) — recomputed to `b2b3a1bd018495ab`; synced `auto-daily-log.md` + skills to the SOP reconcile prompt (graphify-first, per-`[owner/repo]` blocks); fixed `org`→`owner` in the worklog SQL.

## Later

- [ ] Document `enable_nemotron_copilot.py` usage (Tailscale IP, model id) in README.
- [ ] Consider a single config source so `lab-automation/global-claude.md` and the live `llm-prefs` CLAUDE.md cannot drift.

## Done

- [x] Chain a Step 2 reminder onto `scripts/fetch-auto-daily-log.sh` so the git-push hook prompts `/daily-log` (post to `progress-plan#366`) right after Step 1's commit+push succeeds.
- [x] Migrate all LTM references from MySQL/`mysql-memory` MCP to per-user PostgreSQL (`llm-skill-ltm`).
- [x] Add `[owner/repo]` project tags to the bullet contract in `dailylog_md.py`.
- [x] Rewrite `setup-memory.sh` to prefs + base settings only, delegating LTM install.
- [x] Add one-touch `deploy-lab-llm.sh` orchestrator.
- [x] Add `enable_nemotron_copilot.py`.
- [x] Reflect repo rename (`auto-daily-log` → `daily-log`) and skill group in CLAUDE.md.
- [x] Create CONTEXT.md / MEMORY.md / TODO.md project memory files.
- [x] Gitignore local `.claude/settings.json`.
