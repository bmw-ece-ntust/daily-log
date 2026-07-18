---
name: daily-plan
description: Post the morning daily-plan to the BMW Lab progress issue — the user says in plain words what they want to do today, and this turns it into a checklist of measurable targets (no durations yet; the evening /daily-log fills them in). Trigger: /daily-plan, "plan my day", "today I want to ...".
---

# /daily-plan

Post today's **plan** as the day's comment bubble on the lab progress issue —
**before any work starts** (SOP: *"Do not take any action before planning"*).

**The user just says, in plain words, what they want to do today** (the skill
prompt); this skill turns that into a checklist of measurable targets and posts
it. Everything else — yesterday's leftovers, calendar, `TODO.md` — only
*supplements* what the user said. The evening `/daily-log` step later edits this
same comment in place, converting achieved targets into duration bullets with
evidence links.

Lab orgs only (`bmw-ece-ntust`, `bmw-ntust-internship`, `raycg`).
Default target issue: `bmw-ece-ntust/progress-plan#366`. Auth: `gh` CLI.
Timezone: Asia/Taipei (GMT+8).

## Format

Same skeleton as the daily-log [Formatting Standards](https://github.com/bmw-ece-ntust/SOP/blob/master/daily-log.md#formatting-standards),
so the evening log patches it in place — but targets are a checklist and time
ticks are **optional**:

```markdown
### yyyy/mm/dd

**Reviewed by**:

**Short-term Goal**

- [ ] <measurable deliverable>

**Daily-logs**:

- [ ] <target>
- [ ] `hh:mm` : <target>
- [ ] `hh:mm - hh:mm` : <target>
```

Time-tick rules per checklist item:

| Form | When |
| --- | --- |
| `- [ ] <target>` | User hasn't defined today's agenda time for it |
| `` - [ ] `hh:mm` : <target> `` | A **deadline** is known |
| `` - [ ] `hh:mm - hh:mm` : <target> `` | A **duration** is defined (e.g. a meeting) |

- **Targets are measurable deliverables** — an observable output (a figure, a
  passing test, a merged PR, a doc section), never a vague activity
  ("study X", "try Y"). Verb-first, ≤ 12 words.
- **No evidence links at plan time** — links are added in the evening when a
  target is achieved.
- **Short-term Goal** = the day's main target per project, ≤ 10 words.
- Leave `**Reviewed by**:` empty; if the AI drafted the plan, end with the
  `🤖 AI-generated` marker line.

## Step 1 — Guard: one plan per day

Check whether today's comment already exists on the issue:

```bash
gh issue view <issue> -R <owner>/<repo> --json comments \
  --jq '.comments[] | select(.body | startswith("### <yyyy/mm/dd>")) | .url'
```

If it exists, **update it in place** (add missing targets) instead of posting a
second comment. Never duplicate a day.

## Step 2 — Build the targets from the user's prompt

**Primary source — the skill prompt.** Read what the user said they want to do
today and turn each intention into one checklist target. Attach a time tick only
when the user gave one: a stated **deadline** → `` `hh:mm` ``; a fixed slot or
meeting → `` `hh:mm - hh:mm` ``; otherwise leave the target plain (`- [ ] …`).
Rephrase each into a measurable deliverable (verb-first, ≤ 12 words); ask the
user to clarify only if an intention is too vague to state as an output.

If the user typed `/daily-plan` with **no description**, don't invent work —
either ask what they plan to do today, or offer the supplements below as a
starting point and let them pick.

**Supplements (only to enrich what the user said, never to override it):**

1. **Yesterday's entry** on the issue: unfinished goals (`- [ ]` with
   `— pending:` / `— blocked:` reasons) and the `<Upcoming targets>` bullet —
   surface these as roll-forward candidates.
2. **Today's calendar events** (meetings) → `` `hh:mm - hh:mm` `` items. Pull via
   `fill-from-calendar.py` in `$DAILY_LOG_HOME` (needs `env.local.yaml`); skip
   silently if not configured.
3. **`TODO.md` → Now** items of the repo(s) the user mentioned.

## Step 3 — Confirm, then post

Show the composed plan as a draft. Only after the user confirms:

```bash
gh issue comment <issue> -R <owner>/<repo> --body-file <draft>
```

## Hand-off to the evening log

The `/daily-log` posting step (and the `git push` auto flow) must find this
comment and **edit it in place**: each achieved target becomes a
`` `hh:mm - hh:mm` `` duration bullet with its evidence link; unachieved targets
stay `- [ ]` with a ` — pending: <reason>` suffix and roll into the next
morning's plan.

## Safety

Never post without showing the draft and getting confirmation. Never create a
second comment for a day that already has one.

## Reference

- SOP: https://github.com/bmw-ece-ntust/SOP/blob/master/daily-log.md#writing-daily-plan-morning
- Default issue: bmw-ece-ntust/progress-plan#366
