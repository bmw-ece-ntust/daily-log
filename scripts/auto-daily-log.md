Reconcile all 4 project memory files with the current state of the repository, then commit and push.

### Check the knowledge graph first (graphify)

Before reconciling, sync your understanding of the repo from the graphify knowledge graph rather than reading files wholesale:

- If `graphify-out/graph.json` exists, refresh it incrementally (`graphify --update`) and answer the repo's current file list, modules, and architecture with `graphify query` first. Reconcile `AGENTS.md`/`CLAUDE.md` (file list, conventions) and `CONTEXT.md` (architecture, key files) primarily from the graph; read individual files only where the graph cannot answer.
- If it does not exist on a non-trivial repo, build it once with `graphify`, then query it.

This keeps the reconcile token-efficient as the repo grows. If graphify is unavailable, fall back to direct file reads.

### Reconcile the 4 project memory files

These four files at the repo root are the single source of truth for the project. Reconcile each before committing:

- **AGENTS.md / CLAUDE.md** — the static knowledge snapshot. `AGENTS.md` is the tool-neutral base (rules, conventions, file list); `CLAUDE.md` is the tool adapter that defers to it. Update the file list (add new files, fix renamed or deleted entries), terminology, conventions, and external links. Never log session activity or prompting history here.
- **CONTEXT.md** — the living architecture overview. Update the architecture summary, the key files map, external services, and environment notes to match the current repo state.
- **MEMORY.md** — the append-only session log. Append one new dated entry; never edit past entries. Use the form: `### yyyy/mm/dd — [7-digit hash] "<commit title>"`, then `**Duration**: <working hour>` and `**Summary**: <one paragraph>`.
- **TODO.md** — the task backlog. Mark completed items `[x]`, remove stale tasks, add any new tasks uncovered this session, and re-prioritize under **Now / Next / Later**.

### Determine the working hour (per day, from the LTM)

All times are Asia/Taipei (GMT+8). A single push often covers work done across several days, so reconstruct the hours and activities **per day** from the long-term memory (LTM), not from the commit date.

1. Run `git log -1 --format="%H %ai"` for the last commit hash and timestamp (the session-start boundary), and `date "+%Y/%m/%d %H:%M"` for the session end (now).
2. From the LTM, read this repo's `worklog` rows (exact start/end per session) and `activity` rows dated after the last commit, using the `memory` skill (recall-by-repo on `owner` + `repo`). Group them by calendar day.
3. For each day: sum the session durations to get that day's hours, and distil that day's session descriptions into a short activity summary. Cross-check the earliest session against the transcript at `{{VSCODE_TARGET_SESSION_LOG}}`. If both the transcript and the LTM are unavailable, ask *"What time did you start working today?"*. Never invent the time.
4. Write the working hour in the commit body, one line per day:
   - **Single day** collapses to one line: `work duration: yyyy/mm/dd_hh:mm - hh:mm`.
   - **Multiple days** list each day with its range, hours, and activities from the LTM (see the format below).

### Commit and push

1. Write a one-paragraph summary of what was accomplished across the whole span.
2. Remove any LLM from the co-author list.
3. Stage the changed files by name (AGENTS.md/CLAUDE.md, CONTEXT.md, MEMORY.md, TODO.md, plus any others touched); never `git add -A`. Then commit and push using this format (the `work duration` block has one line per day, sourced from the LTM):

---

<Short imperative summary title>

work duration:
- yyyy/mm/dd_hh:mm - hh:mm (N.Nh): <what was done that day, from the LTM>
- yyyy/mm/dd_hh:mm - hh:mm (N.Nh): <what was done that day, from the LTM>

Summary:
<One-paragraph summary of what changed and why>

Details:
1. <Specific change 1>
2. <Specific change 2>
