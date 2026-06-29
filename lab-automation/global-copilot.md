# Global Copilot Instructions — ijosh-ch

## Long-Term Memory (PostgreSQL)

The lab LTM is a **per-user PostgreSQL** store on the BMW Lab box, reached over an SSH tunnel and managed by the [`llm-skill-ltm`](https://github.com/bmw-ece-ntust/llm-skill-ltm) repo (replaces the old MySQL setup). No raw prompts/responses are stored — only distilled knowledge plus `activity`/`worklog` rows attributed by GitHub account, with `owner` (the account, org or personal) and `repo` (name only) kept as separate `metadata` fields.

**At the START of every session**, recall recent work for the current project (recall-by-repo):

```sql
SELECT metadata->>'date', metadata->>'machine', metadata->>'branch', type, description
FROM memory
WHERE metadata->>'owner' = :'owner' AND metadata->>'repo' = :'repo'
ORDER BY metadata->>'date' DESC;
```

Session activity and worklog rows (with exact start/end timestamps) are recorded automatically by the `llm-skill-ltm` SessionStart hook and `stm-backup.sh` — no manual inserts. Use the `worklog` start/end times when generating daily-log bullets. Full design: [bmw-ece-ntust/llm-skill-ltm — docs/ARCHITECTURE.md](https://github.com/bmw-ece-ntust/llm-skill-ltm/blob/master/docs/ARCHITECTURE.md).

## Identity

- GitHub: ijosh-ch / Ian Joseph Chandra
- Email: ianjoseph2204@gmail.com
- Lab: BMW Lab, NTUST — Supervisor: Prof. Ray
- Daily-log issue: bmw-ece-ntust/progress-plan#366
- Timezone: Asia/Taipei (GMT+8)
