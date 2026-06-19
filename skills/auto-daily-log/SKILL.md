---
name: auto-daily-log
description: Post BMW Lab daily-log entries to the GitHub Projects progress issue (default bmw-ece-ntust/progress-plan#366) using the bmw-ece-ntust/daily-log tool. Seeds entries from long-term memory session records and commit history, restricted to orgs bmw-ece-ntust, bmw-ntust-internship, and raycg. Catches up missing weekdays, logs today, records sick leave/holiday, reorders comments, generates a missing-days reminder, and attaches documentation evidence links. This is the posting step (separate from daily-log-commit). Trigger: /auto-daily-log
---

# /auto-daily-log

Publish daily-log entries to the lab progress issue using
https://github.com/bmw-ece-ntust/daily-log. The **commit** step is the
separate `daily-log-commit` skill; run this **after** committing, to post.

## Eligible orgs (hard restriction)

Only repos under **`bmw-ece-ntust`**, **`bmw-ntust-internship`**, and **`raycg`**
count as daily-log progress. Ignore activity in any other org/account. Set
`env.yaml`'s configured orgs to exactly these three.

Default target issue: `bmw-ece-ntust/progress-plan#366`. Auth: `gh` CLI.

## Step 1 — Ensure the tool is ready

This repo (`bmw-ece-ntust/daily-log`) **is** the tool; `install.sh` sets
`DAILY_LOG_HOME` and the venv. Just ensure it:

```bash
TOOL="${DAILY_LOG_HOME:-$HOME/Documents/GitHub/daily-log}"
[ -d "$TOOL/.git" ] || git clone https://github.com/bmw-ece-ntust/daily-log.git "$TOOL"
git -C "$TOOL" pull --ff-only 2>/dev/null || true
[ -d "$TOOL/.venv" ] || python3 -m venv "$TOOL/.venv"
"$TOOL/.venv/bin/pip" install -q -r "$TOOL/requirements.txt"
[ -f "$TOOL/env.yaml" ] || cp "$TOOL/env.example.yaml" "$TOOL/env.yaml"
```

Run tool commands from `$TOOL` with `"$TOOL/.venv/bin/python"`. Calendar features
need `$TOOL/env.local.yaml` (iCal URL); if missing and a calendar action is asked,
request the URL first.

## Step 2 — Cross-reference LTM + GitHub commits (accuracy)

Build each day's detail from two sources of truth, then attach evidence.

1. **LTM worklogs** give the accurate working hours + repos/branches per day (exact
   `start`/`end` from the session). Run via `bash "$LTM_HOME/scripts/pg-memory-conn.sh"` + psql:

   ```sql
   SELECT metadata->>'date' AS d, metadata->>'repo' AS repo, metadata->>'branch' AS branch,
          min(metadata->>'start') AS started, max(metadata->>'end') AS ended
   FROM memory
   WHERE type='worklog' AND metadata->>'user' = '<gh-user>'
     AND metadata->>'org' IN ('bmw-ece-ntust','bmw-ntust-internship','raycg')
     AND metadata->>'date' >= '<since>'
   GROUP BY 1,2,3 ORDER BY d;
   ```
   (`session`/`activity` rows supplement days without a worklog; `session.doc_url` is a ready evidence link.)

2. **GitHub commits** give the concrete deliverable + the SOP evidence link:

   ```bash
   gh api "repos/<owner>/<repo>/commits?author=<gh-user>&since=<dayT00:00>&until=<dayT23:59>" \
     --jq '.[] | .sha[0:7] + "  " + (.commit.message | split("\n")[0])'
   ```
   Use the 7-digit sha for the evidence link (`.../tree/<7hex>#<section>`).

3. **Verify + compose**: the `HH.MM – HH.MM` tick comes from the **worklog** (accurate
   hours), the bullet text + evidence link come from the **commit**. A bullet is
   corroborated when LTM work on a repo is backed by a commit on that repo the same
   day. LTM-only days (worked via LLM, no commit) are still logged from the worklog
   interval, flagged as lacking commit evidence. Commit-only days are seeded by the tool.

## Step 3 — Map the request to a command

If no `--since` date is given, ask (or infer the last logged day). ALWAYS dry-run,
show output, confirm, then re-run with the apply flag.

| Intent | Dry-run | Apply |
| --- | --- | --- |
| Catch up since DATE | `main.py --since DATE --ensure-comments --seed-from-commits --skip-if-no-activity` | add `--apply`, then `reorder-comments.py --since DATE --until today --apply` |
| Fill from commits only | same as above | add `--apply` |
| Fill from calendar only | `fill-from-calendar.py --since DATE` | add `--create` |
| Reorder chronologically | `reorder-comments.py --since DATE --until today` | add `--apply` (200+ comments — confirm explicitly) |
| Reminder | `main.py --generate-reminder reminder.md --since DATE` | read-only; then show it |
| Log today / specific day | compose entry, then post | — |

Single-day / sick leave / holiday: `### YYYY/MM/DD` heading, `HH.MM` dot ticks,
evidence links. Sick leave = `` `SICK LEAVE` ``; holiday = `` `HOLIDAY` ``.

## Step 4 — Safety

Default to dry-run; never `--apply`/`--create` until the user has seen the dry-run
and confirmed. Reorder deletes+recreates 200+ comments — require explicit
confirmation. After applying, show `reminder.md` (remaining gaps, bullets missing
evidence).

## Reference

- Tool: https://github.com/bmw-ece-ntust/daily-log
- SOP: https://github.com/bmw-ece-ntust/SOP/blob/master/daily-log.md#auto-daily-log
- Default issue: bmw-ece-ntust/progress-plan#366
