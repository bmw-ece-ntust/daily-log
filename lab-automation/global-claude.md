# Global Claude Instructions — ijosh-ch

Applied to every project. Do not override project-level CLAUDE.md — they stack.

---

## Long-Term Memory (MySQL)

A `mysql-memory` MCP tool is globally configured in `~/.claude/settings.json`.
It connects directly to `llm_memory` on the BMW Lab VM at `140.118.122.119:3306`.
Verify connectivity with `nc -z 140.118.122.119 3306`.

**Every session, at START — load recent context:**

```sql
SELECT s.id, s.repo, s.start_at, s.end_at, s.commit_title, ss.summary
FROM sessions s
LEFT JOIN session_summaries ss ON ss.session_id = s.id
ORDER BY s.start_at DESC
LIMIT 5;
```

**Every session, at END — before the git commit:**

1. `git config user.name` and `git config user.email` → committer identity
2. `git remote get-url origin` → repo name (strip to `owner/repo`)
3. `git log -1 --format="%H %ai"` → base commit hash + timestamp
4. INSERT into `sessions`: github_username, github_email, repo, start_at, end_at, base_commit, commit_title
5. INSERT one row per key exchange into `prompts`: session_id, tool (`claude`), prompted_at, prompt_summary, response_summary
6. INSERT into `session_summaries`: session_id, summary (one paragraph — reused as git commit "Summary" field)
7. After push: `UPDATE sessions SET result_commit = '<new_hash>' WHERE id = <sid>;`

Full schema: [bmw-ece-ntust/SOP — lab-automation/llm-memory.md](https://github.com/bmw-ece-ntust/SOP/blob/master/lab-automation/llm-memory.md)

---

## Identity

- GitHub: ijosh-ch / Ian Joseph Chandra
- Email: ianjoseph2204@gmail.com
- Lab: BMW Lab, NTUST — Supervisor: Prof. Ray
- Daily-log issue: bmw-ece-ntust/progress-plan#366
- Timezone: Asia/Taipei (GMT+8)
