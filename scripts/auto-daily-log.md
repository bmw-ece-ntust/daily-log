Reconcile all 4 project memory files with the current state of the repository.

**CLAUDE.md** — check file list (add new files, update renamed/deleted entries), terminology, conventions, and external links. This is a static knowledge snapshot for LLMs — do not log session activity or prompting history.

**CONTEXT.md** — update architecture overview, key files map, and any changed external services or environment notes to reflect the current repo state.

**MEMORY.md** — append a new dated entry (`### yyyy/mm/dd`) summarizing decisions made, patterns established, or gotchas discovered this session. Do not edit past entries.

**TODO.md** — mark completed items as `[x]`, remove stale tasks, and add any new tasks uncovered this session. Re-prioritize if needed under **Now / Next / Later**.

Then:

1. Run `git log -1 --format="%H %ai"` (= session START boundary) and `date "+%Y/%m/%d %H:%M"` (= session END).
   Read the VS Code session log at `{{VSCODE_TARGET_SESSION_LOG}}` to find the first user message timestamp that falls after the last commit — that is the true session start. If unavailable, ask: *"What time did you start working today?"*
2. Format the work duration as `yyyy/mm/dd_hh:mm - yyyy/mm/dd_hh:mm` (session start datetime to end datetime; e.g. `2026/06/18_14:07 - 2026/06/19_16:25`).
3. Write a one-paragraph summary of what was accomplished this session.
4. Remove any LLMs from the co-author list.
5. Stage all changes including CLAUDE.md, CONTEXT.md, MEMORY.md, and TODO.md, then commit and push using this format:

---

<Short imperative summary title>

work duration: <yyyy/mm/dd_hh:mm - yyyy/mm/dd_hh:mm>

Summary:
<One-paragraph summary of what changed and why>

Details:
1. <Specific change 1>
2. <Specific change 2>
