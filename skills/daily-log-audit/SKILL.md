---
name: daily-log-audit
description: Full-history audit of the GitHub daily-log (progress-plan#366) against the current SOP format — mechanical conformance checks, rewrite failing days in place, fill missing days (pass --since for a quick gap-check). Trigger: /daily-log-audit, "audit / verify / fix my daily log".
---

# /daily-log-audit

Audits the **entire daily-log history** against the current SOP
[Formatting Standards](https://github.com/bmw-ece-ntust/SOP/blob/master/daily-log.md#formatting-standards)
and repairs it: old entries written under earlier formats are rewritten in place,
missing days are filled. Where `verify-daily-log` only *filled gaps* since a date,
this skill also *re-formats what already exists* — run it after the SOP format
changes, or to bring the whole log to one consistent standard.

Lab orgs only (`bmw-ece-ntust`, `bmw-ntust-internship`, `raycg`).
Issue: `bmw-ece-ntust/progress-plan#366`. Timezone: Asia/Taipei (GMT+8).

## Scope

- **Default (full audit)**: from the **beginning of the LTM** to today. The epoch is
  the earliest LTM row:

  ```sql
  SELECT min(metadata->>'date') FROM memory
  WHERE type IN ('worklog','activity') AND metadata->>'user' = '<gh-user>'
    AND metadata->>'owner' IN ('bmw-ece-ntust','bmw-ntust-internship','raycg');
  ```

  If the log has comments older than the LTM epoch, extend the scope back to the
  oldest `### yyyy/mm/dd` comment — those days get format-checked too (times taken
  as-written, since no LTM exists to verify them against).
- **`--since <date>`**: audit only from that date (this is the old
  `verify-daily-log` behaviour plus conformance rewriting).

## Token-efficient workflow (mechanical triage, LLM only for failures)

Conformance is decided by cheap local checks over data fetched once; the LLM
composes text only for days that fail. Cost scales with the number of bad days,
not the length of the history.

### 1. Gather — no LLM

- **All day comments, one fetch** (paginate; cache to a scratch file):

  ```bash
  gh api "repos/bmw-ece-ntust/progress-plan/issues/366/comments" --paginate \
    --jq '.[] | {id: .id, url: .html_url, body: .body}'
  ```

- **LTM truth per day** (working intervals + repos), one query over the whole scope:

  ```sql
  SELECT metadata->>'date', metadata->>'owner' || '/' || (metadata->>'repo'),
         min(metadata->>'start'), max(metadata->>'end')
  FROM memory WHERE type='worklog' AND metadata->>'user' = '<gh-user>'
    AND metadata->>'owner' IN ('bmw-ece-ntust','bmw-ntust-internship','raycg')
    AND metadata->>'date' >= '<epoch>' GROUP BY 1,2 ORDER BY 1;
  ```

  (`activity` rows supplement days with no worklog; `session.doc_url` supplies
  ready evidence links.)

- **Commit-side evidence**: the tool's reminder covers missing days + missing links:
  `"$TOOL/.venv/bin/python" main.py --generate-reminder reminder.md --since <epoch>`.

### 2. Triage every day — no LLM

Classify each day in scope by mechanical checks (regex over the cached comment
bodies; a small scratch script, not per-day LLM calls):

| Status | Meaning |
| --- | --- |
| `OK` | Comment exists, all conformance checks pass, times match LTM |
| `REWRITE` | Comment exists but fails ≥ 1 conformance check |
| `MISSING` | LTM/commits show work but no comment (the old verify gap) |
| `SKIP` | No work, or `SICK LEAVE` / `HOLIDAY` / `ABSENT` marker present |

**Conformance checks (current SOP):**

1. Heading `### yyyy/mm/dd`; exactly **one comment per day**; `**Reviewed by**:` line present.
2. **Short-term Goal** = one plain line, ≤ 10 words.
3. Every bullet is `` `HH.MM - HH.MM` [owner/repo]: [<achieved target>](link) `` —
   verb-first, past tense, ≤ 12 words before the link.
4. Evidence links point at **study-notes documentation at the commit**
   (`.../tree/<7hex>#<section>`) — flag any bare `/commit/<hash>` link.
5. **No sub-bullets**; bulk commits collapsed to one bullet; consecutive
   same-`[owner/repo]` intervals merged into one bullet with an extended end time.
6. Bullet times fall inside an LTM worklog interval for that repo-day (±15 min
   tolerance); unknown starts written `??:?? - HH.MM`, never invented.
7. Only lab-org `[owner/repo]` tags.

Emit the triage as a compact table: `date | status | reasons`. **Only `REWRITE`
and `MISSING` days move to step 3.**

### 3. Rewrite / fill — minimal LLM

- **`REWRITE` days**: recompose the comment body in the current SOP format from
  three inputs — the existing body (preserve achieved targets, `Reviewed by` value,
  and any human-written notes), the LTM intervals (authoritative times), and the
  commit evidence links. Distil old verbose bullets to target-first ≤ 12 words;
  fold sub-bullets into their parent; replace `/commit/<hash>` links with the
  `tree/<7hex>#<section>` form (resolve via the tool's `--link-to-files`). Never
  drop information that has no new home — carry it into the linked study-notes or
  flag it in the report.
- **`MISSING` days**: compose fresh entries exactly as `daily-log` Step 2 does
  (hourly summary bullets; LTM-only intervals flagged "no documentation evidence").
- **Edit in place** via the comment id (`gh api --method PATCH .../comments/<id>`);
  create a new comment only for `MISSING` days. Never leave two comments for one day.

### 4. Apply + report

Dry-run first: show the triage table and, for each `REWRITE` day, an old→new body
diff. Only after explicit confirmation, apply the edits **in batches of ~10 days**
(oldest first), reporting progress per batch so an interruption loses little. Finish
with `reorder-comments.py --since <epoch> --until today` (dry-run → confirm →
`--apply`) if order changed, and report:
**days audited / OK / rewritten / filled / skipped / still missing evidence**.

## Safety

Read-only until the triage table and diffs are shown and the user confirms. A full
audit touches the whole history — hundreds of comments — so always show the
`REWRITE` count before applying, apply in batches, and require a separate explicit
confirmation for the reorder step. `Reviewed by` values written by humans are never
cleared. Verify-only run (`--check`) posts nothing.
