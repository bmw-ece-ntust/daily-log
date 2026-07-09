# Global Claude Instructions — BMW Lab AI Preferences

Lab AI preferences, mirrored from [`bmw-ece-ntust/llm-core`](https://github.com/bmw-ece-ntust/llm-core). Installed by `setup-memory.sh` to `~/.claude/CLAUDE.md`, where Claude Code and Cowork load it as user-global memory. Applied to every project; project-level `CLAUDE.md` files stack on top and take precedence.

---

## Long-Term Memory (PostgreSQL)

The lab LTM is a **per-user PostgreSQL** store on the BMW Lab box, reached over an SSH tunnel and managed by the [`llm-skill-ltm`](https://github.com/bmw-ece-ntust/llm-skill-ltm) repo. The `memory` skill (installed into `~/.claude/skills`) recalls and stores rows; a SessionStart hook records activity automatically. No raw prompts/responses are stored — only distilled knowledge plus `activity`/`worklog` rows attributed by GitHub account, with `owner` (the account, org or personal) and `repo` (name only) kept as separate `metadata` fields.

**Every session, at START — recall recent work for the current project (recall-by-repo):**

```sql
SELECT metadata->>'date', metadata->>'machine', metadata->>'branch', type, description
FROM memory
WHERE metadata->>'owner' = :'owner' AND metadata->>'repo' = :'repo'
ORDER BY metadata->>'date' DESC;
```

Activity (`activity` per repo/day) and worklog (`worklog` per session, exact start/end timestamps) rows are written automatically by the `llm-skill-ltm` SessionStart hook and `stm-backup.sh` — no manual inserts. Use the `worklog` start/end times when generating daily-log bullets.

Full design: [bmw-ece-ntust/llm-skill-ltm — docs/ARCHITECTURE.md](https://github.com/bmw-ece-ntust/llm-skill-ltm/blob/master/docs/ARCHITECTURE.md). SOP overview: [SOP — lab-automation/llm-memory.md](https://github.com/bmw-ece-ntust/SOP/blob/master/lab-automation/llm-memory.md)

---

## Identity

- GitHub: ijosh-ch / Ian Joseph Chandra
- Email: ianjoseph2204@gmail.com
- Lab: BMW Lab, NTUST — Supervisor: Prof. Ray
- Daily-log issue: bmw-ece-ntust/progress-plan#366
- Timezone: Asia/Taipei (GMT+8)
