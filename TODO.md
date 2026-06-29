# TODO.md — daily-log

Prioritized task list. `[x]` = done, `[ ]` = open.

---

## Now

- [ ] Verify `deploy-lab-llm.sh` end-to-end on a clean macOS machine (clone → prefs → LTM → daily-log install → optional `--backfill`).
- [ ] Confirm `install.sh` wires the `UserPromptSubmit` daily-log hook correctly when `~/.claude/settings.json` already exists (jq merge path).

## Next

- [ ] Backfill `[owner/repo]` tags on existing `progress-plan#366` comments that predate the tag format.
- [ ] Update `README.md` Quick Claude Prompts to mention the three skills (`/daily-log`, `/daily-log-commit`, `/verify-daily-log`).
- [ ] Re-check `.sop-hash` against the current SOP `## Auto Daily-log` section after the format changes (tags + `HH.MM`).

## Later

- [ ] Document `enable_nemotron_copilot.py` usage (Tailscale IP, model id) in README.
- [ ] Consider a single config source so `lab-automation/global-claude.md` and the live `llm-prefs` CLAUDE.md cannot drift.

## Done

- [x] Migrate all LTM references from MySQL/`mysql-memory` MCP to per-user PostgreSQL (`llm-skill-ltm`).
- [x] Add `[owner/repo]` project tags to the bullet contract in `dailylog_md.py`.
- [x] Rewrite `setup-memory.sh` to prefs + base settings only, delegating LTM install.
- [x] Add one-touch `deploy-lab-llm.sh` orchestrator.
- [x] Add `enable_nemotron_copilot.py`.
- [x] Reflect repo rename (`auto-daily-log` → `daily-log`) and skill group in CLAUDE.md.
- [x] Create CONTEXT.md / MEMORY.md / TODO.md project memory files.
- [x] Gitignore local `.claude/settings.json`.
