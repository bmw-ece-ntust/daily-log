---
name: verify-daily-log
description: Quickly verify the GitHub daily-log (progress-plan#366) is complete and accurate by cross-checking GitHub commit history + LTM worklogs, then fill only the missing days. Token-efficient, the gap is computed from structured data (SQL + gh + the tool's reminder), and the LLM only composes text for missing days. Trigger: /verify-daily-log
---

# /verify-daily-log

Verifies the daily-log against **two sources of truth**, GitHub commits (proof of
deliverables) and LTM worklogs (proof of when/what you worked on), and fills only the
gaps. Lab orgs only (`bmw-ece-ntust`, `bmw-ntust-internship`, `raycg`). Issue:
`bmw-ece-ntust/progress-plan#366`.

## Why two sources

- **Commits** prove a concrete deliverable and give the SOP evidence link (7-digit hash).
- **LTM worklogs** prove the *working hours* and *which repos*, including LLM sessions
  that produced no commit. Neither alone is complete; together they're accurate.

## Token-efficient workflow (verify fast, compose only for gaps)

The heavy comparison runs on cheap structured data. The LLM only writes text for the
few missing days, so cost scales with the gap, not the history.

### 1. Gather — no LLM
- **Commit-side gaps**: in the tool (`$DAILY_LOG_HOME` or the cache),
  `"$TOOL/.venv/bin/python" main.py --generate-reminder reminder.md --since <date>`.
  `reminder.md` is a small file: missing days + bullets lacking evidence.
- **LTM-side days** (work even without a commit):
  ```bash
  CONN="$(bash "$LTM_HOME/scripts/pg-memory-conn.sh")"; PSQL="$(brew --prefix libpq)/bin/psql"
  "$PSQL" "$CONN" -tAF'|' -c "SELECT metadata->>'date', metadata->>'repo',
       min(metadata->>'start'), max(metadata->>'end')
     FROM memory WHERE type='worklog' AND metadata->>'user'='<gh-user>'
       AND metadata->>'org' IN ('bmw-ece-ntust','bmw-ntust-internship','raycg')
       AND metadata->>'date' >= '<date>' GROUP BY 1,2 ORDER BY 1"
  ```

### 2. Diff — no LLM
`working_days = commit_days ∪ ltm_worklog_days`. `gaps = working_days` that are
missing or incomplete in the log (from `reminder.md`). **Skip days already complete**
(logged + evidence present). Only the gap list moves forward — this is the speed.

### 3. Fill only the gaps — minimal LLM
For each gap day compose the SOP entry:
- `HH.MM – HH.MM` tick(s) from the **worklog** interval(s) (accurate hours).
- bullet text + evidence link from that day's **commits**
  (`gh api repos/<repo>/commits?author=<me>&since=<day>&until=<day+1>`), evidence =
  `.../tree/<7hex>#<section>`.
- LTM-only day (no commit) → log the interval, flag "no commit evidence".

### 4. Apply + report
Dry-run, show the gap list, confirm, then post: `main.py --since <date>
--ensure-comments --seed-from-commits --skip-if-no-activity --apply`, add manual
entries for LTM-only days, and `reorder-comments.py --apply` if order changed. Report:
**days checked / already complete / filled / still missing evidence**.

## Safety

Read-only by default. Never `--apply` until the gap list is shown and confirmed. The
reorder rewrites 200+ comments — confirm explicitly. Verify-only run posts nothing.
