---
name: daily-log-commit
description: Run the BMW Lab daily-log COMMIT step when the user genuinely intends to commit/push (a short "git push" / "commit and push" instruction). Reconciles the 4 project files, commits in SOP work duration format, pushes, and writes a long-term-memory session record. Do NOT trigger when "git push" merely appears inside a longer sentence that is about something else. Trigger: /daily-log-commit
---

# /daily-log-commit

The commit half of the BMW Lab daily-log SOP. (The posting half is `daily-log`.)

## When to run

Only when the user's message is, in substance, the instruction to commit/push —
e.g. "git push", "commit and push", "push my changes". If "git push" appears
mid-sentence while the user is discussing something else (describing a skill,
asking a question), do **not** run this. This is the smart-trigger fix for the
old hook that fired on any literal match.

## Workflow

1. **Reconcile the 4 files** against the repo: `AGENTS.md`/`CLAUDE.md` (tool-neutral
   base + adapter: file list, conventions, no session log), `CONTEXT.md`
   (architecture/services), `MEMORY.md` (append a new entry
   `### yyyy/mm/dd — [7-digit hash] "<title>"` with `**Duration**` + `**Summary**`,
   never edit past ones), `TODO.md` (check off done, add new, re-prioritize
   Now/Next/Later).
2. **Working hour, per day, from the LTM** (Asia/Taipei): `git log -1 --format="%H %ai"`
   is the last-commit boundary; `date "+%Y/%m/%d %H:%M"` is the end. A single push can
   cover several days, so recall this repo's `worklog`/`activity` rows after the last
   commit (the `memory` skill, recall-by-repo on `owner`+`repo`), group them by calendar
   day, and for each day sum the hours and distil the activities. The whole-span start is
   the first user-message timestamp after the last commit (the UserPromptSubmit hook
   injects the transcript path); ask only if transcript and LTM are both unavailable.
3. **Stage by name** (never `git add -A`); keep `.claude/settings.local.json` out.
   The `.githooks/pre-commit` hook auto-scrubs session-noise/secrets from
   `.claude/settings.json` on commit, so no manual revert is needed; just confirm
   the hook ran ("scrubbed session-noise") if that file was staged.
4. **Commit** in the SOP format, no LLM co-author. The `work duration` block has one
   line per day (single-day work collapses to one `work duration: ... ` line):
   ```
   <Short imperative summary title>

   work duration:
   - yyyy/mm/dd_hh:mm - hh:mm (N.Nh): <what was done that day, from the LTM>
   - yyyy/mm/dd_hh:mm - hh:mm (N.Nh): <what was done that day, from the LTM>

   Summary:
   <one paragraph>

   Details:
   1. <change 1>
   2. <change 2>
   ```
5. **Push** (`git push origin <branch>`).
6. **Write a memory session record** (see the `memory` skill) so `daily-log`
   can later build the daily entry. Only if the repo is LTM-eligible per
   `ltm_eligible` — its org is one of `bmw-ece-ntust`, `bmw-ntust-internship`,
   `raycg`, OR its slug (owner/repo) is listed in `LAB_REPOS` in `lab.config`
   (currently `ijosh-ch/claude`, the personal preference repo adopted as the
   lab's preference foundation):
   ```
   type=session  name=<repo>-<yyyymmdd>-<7hex>
   description=<commit title>
   body=<distilled: what was done, decisions, gotchas — NOT raw prompts/responses>
   metadata={"user":"<gh api user --jq .login>","machine":"<hostname -s>","repo":"<owner/repo>","org":"<org>","branch":"<git branch --show-current>","date":"YYYY-MM-DD","commit":"<7hex>","doc_url":"<doc header link with 7-digit hash, if any>"}
   ```
   Detect org + repo from `git remote get-url origin`, branch from
   `git branch --show-current`, and the GitHub username from `gh api user --jq .login`
   (lab performance is attributed by GitHub account). If the repo is not
   LTM-eligible (org not a lab org and slug not in `LAB_REPOS`), skip the memory write.
   This is the distilled "knowledge" layer; the SessionStart `record-session.sh` hook
   already logs the lightweight "activity" layer (repo/branch/day) automatically.
   The `memory` skill and `record-session.sh` are provided by the
   `bmw-ece-ntust/llm-skill-ltm` repo (install it for the memory write to work).

## Notes

- This is the only auto-commit path; typing the push instruction is explicit intent.
- Tier-1 offline (memory) does not block the commit — push anyway, skip step 6.
