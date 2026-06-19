---
name: daily-log-commit
description: Run the BMW Lab daily-log COMMIT step when the user genuinely intends to commit/push (a short "git push" / "commit and push" instruction). Reconciles the 4 project files, commits in SOP work duration format, pushes, and writes a long-term-memory session record. Do NOT trigger when "git push" merely appears inside a longer sentence that is about something else. Trigger: /daily-log-commit
---

# /daily-log-commit

The commit half of the BMW Lab daily-log SOP. (The posting half is `auto-daily-log`.)

## When to run

Only when the user's message is, in substance, the instruction to commit/push —
e.g. "git push", "commit and push", "push my changes". If "git push" appears
mid-sentence while the user is discussing something else (describing a skill,
asking a question), do **not** run this. This is the smart-trigger fix for the
old hook that fired on any literal match.

## Workflow

1. **Reconcile the 4 files** against the repo: `CLAUDE.md` (file list/conventions,
   no session log), `CONTEXT.md` (architecture/services), `MEMORY.md` (append a
   new `### yyyy/mm/dd` entry, never edit past ones), `TODO.md` (check off done,
   add new, re-prioritize Now/Next/Later).
2. **Session timing**: `git log -1 --format="%H %ai"` is the last-commit boundary;
   `date "+%Y/%m/%d %H:%M"` is the end. The session start is the first user-message
   timestamp in the VS Code transcript that falls after the last commit (the
   UserPromptSubmit hook injects the transcript path). Ask only if unavailable.
3. **Stage by name** (never `git add -A`); keep `.claude/settings.local.json` out.
   The `.githooks/pre-commit` hook auto-scrubs session-noise/secrets from
   `.claude/settings.json` on commit, so no manual revert is needed; just confirm
   the hook ran ("scrubbed session-noise") if that file was staged.
4. **Commit** in the SOP format, no LLM co-author:
   ```
   <Short imperative summary title>

   work duration: <yyyy/mm/dd_hh:mm - yyyy/mm/dd_hh:mm>

   Summary:
   <one paragraph>

   Details:
   1. <change 1>
   2. <change 2>
   ```
5. **Push** (`git push origin <branch>`).
6. **Write a memory session record** (see the `memory` skill) so `auto-daily-log`
   can later build the daily entry. Only if the repo's org is one of
   `bmw-ece-ntust`, `bmw-ntust-internship`, `raycg` (others are not daily-log progress):
   ```
   type=session  name=<repo>-<yyyymmdd>-<7hex>
   description=<commit title>
   body=<distilled: what was done, decisions, gotchas — NOT raw prompts/responses>
   metadata={"user":"<gh api user --jq .login>","machine":"<hostname -s>","repo":"<owner/repo>","org":"<org>","branch":"<git branch --show-current>","date":"YYYY-MM-DD","commit":"<7hex>","doc_url":"<doc header link with 7-digit hash, if any>"}
   ```
   Detect org + repo from `git remote get-url origin`, branch from
   `git branch --show-current`, and the GitHub username from `gh api user --jq .login`
   (lab performance is attributed by GitHub account). If the org is outside the three,
   skip the memory write.
   This is the distilled "knowledge" layer; the SessionStart `record-session.sh` hook
   already logs the lightweight "activity" layer (repo/branch/day) automatically.
   The `memory` skill and `record-session.sh` are provided by the
   `bmw-ece-ntust/llm-skill-ltm` repo (install it for the memory write to work).

## Notes

- This is the only auto-commit path; typing the push instruction is explicit intent.
- Tier-1 offline (memory) does not block the commit — push anyway, skip step 6.
