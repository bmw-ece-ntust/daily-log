---
name: daily-plan
description: Post the morning daily-plan to the BMW Lab progress issue — the user says in plain words what they want to do today, and this turns it into a checklist of measurable targets (no durations yet; the evening /daily-log fills them in). After posting, gives a LINE "Daily Plan" draft for the lab group. Trigger: /daily-plan, "plan my day", "today I want to ...".
---

## Model — Sonnet 5 for the writing (mandatory)

Same rule as `daily-log`: delegate the composition to the Sonnet-pinned
`project-analyst` sub-agent (or an `Agent` call with `model: "sonnet"`) and keep the
confirm-and-post loop in the main session. Claude cannot switch its own session model,
so delegation is how "run this on Sonnet 5, then carry on as before" is actually done.
See `skills/daily-log/SKILL.md` for the full statement.


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
Target issue: your own daily-log issue (`PREFS_DAILYLOG_ISSUE` in `~/.claude/identity.sh`; Ian's is `bmw-ece-ntust/progress-plan#366`). Auth: `gh` CLI.
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
   silently if not configured. Events tagged `action-sync:` are execution-plan
   blocks, not meetings; the script leaves them out.
3. **`TODO.md` → Now** items of the repo(s) the user mentioned.
4. **The execution plan** (the `Execution Plan` comment in the Thesis Discussion
   issue): today's row of the Weekly plan, plus the next items of the pull-forward
   queue.

**A priority change is a re-plan.** When what the user says today reorders the
plan (for example, "finish the related-work part first today"), post the day's plan
as usual, then run **`/action-sync` Step 6**. It re-sorts the queue, re-fits the days
within capacity, and moves the deadlines. A pending item keeps its missed date struck
through; a future item's date is just replaced. It shows the diff and, on a yes,
moves the Google Calendar events to match.

## Step 3 — Confirm, then post

Show the composed plan as a draft. Only after the user confirms:

```bash
gh issue comment <issue> -R <owner>/<repo> --body-file <draft>
```

**Concise and precise (the member's rule, 10/08).** Each item is one line:
`` `hh.mm - hh.mm` : <outcome in the paper, ≤ 12 words> ([mm/dd Prof. <Name>](<minutes link>)) ``.
- **Outcome.** Name the section and what it will say or show. Leave out the reasoning:
  the minutes behind the link carry it.
- **Reference.** A short one, for the meeting the target comes from:
  `([10/06 Prof. Gu](…))`, or `([10/07 minutes](…))` when no professor is named.
- **Times.** Split a slot around lunch instead of covering it
  (`` `11.00 - 11.30`, `12.30 - 13.30` ``).
- **Example.** Too long:
  `Sec. I-A3 Dynamic RA-RU Allocation and Transient Analysis finished: why reservation
  makes R_i vary, and why only a transient model captures it`. Right:
  `Sec. I-A3 dynamic RA-RU allocation finished ([10/06 Prof. Gu](…))`.
- **LINE summary lines** follow the same rule, with the reference in brackets and no
  link: `Sec. 1.1: finish the dynamic RA-RU part (10/06 Prof. Gu)`.

## Step 4 — LINE draft for the lab group (always)

After the plan is posted, give the member the LINE message for it, without being asked:

```
yyyy/mm/dd: Daily Plan

<html_url of the day's #366 comment>

Summary:
1. <the day's first target, as paper text>
2. <next target>
```

- **Summary.** One line per main target, 1 to 4 lines, in priority order. Name the
  minutes that asked for a target when that is why it comes first ("from the 10/06
  meeting with Prof. Gu").
- **Today's targets, not yesterday's meeting summary.** The 10/07 Daily Plan repeated
  the 10/06 meeting summary word for word, so the group could not see what the day was
  for.

**The rules every LINE draft follows**, taken from the member's own messages in the lab
group (10/02 to 10/07):
- **Header.** The first line is `yyyy/mm/dd: <Kind>`, where the kind is `Daily Plan`,
  `Daily Progress` or `Meeting with Prof. <Name>`.
- **Link.** Then a blank line and the GitHub comment the message is about: the day's #366
  comment for a plan or progress, the #489 minutes comment for a meeting.
- **Summary.** Then `Summary:` and 1 to 4 numbered lines.
- **Results.** Only a Daily Progress adds `Results:` with the Overleaf link.
- **Paper text, not activity.** Each line names paper text: the section, paragraph or
  table, in the member's own numbering (`Sec. 1.1 Related Work`, `Sec. 1.2
  Contributions`). Prof. Ray told the group on 10/02: *"Read paper is NOT your goal.
  Stick your goal on the paper."* So "Read X" is never a summary line. What reading
  produced, such as a row of the comparison table or a sentence of Section I, is.
- **Draft only.** Give one fenced block, ready to paste, and never send it. The member
  posts it. A mention such as `@Pengwenlong Gu` cannot be made from the text; tell the
  member to tag the professor in LINE.

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
- Issue: the member's own, `PREFS_DAILYLOG_ISSUE` (Ian's: bmw-ece-ntust/progress-plan#366)
