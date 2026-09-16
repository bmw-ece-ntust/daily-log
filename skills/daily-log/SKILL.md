---
name: daily-log
description: Post BMW Lab daily-log entries to the GitHub Projects progress issue (default bmw-ece-ntust/progress-plan#366) using the bmw-ece-ntust/daily-log tool. First runs the daily-log-commit (git push) workflow for every lab-related local repo with pending changes, then posts. Seeds entries from long-term memory session records and commit history, restricted to orgs bmw-ece-ntust, bmw-ntust-internship, and raycg. Updates the existing daily-plan/daily-log comment for the day in place; creates a new day comment only when none exists. Catches up missing weekdays, logs today, records sick leave/holiday, reorders comments, generates a missing-days reminder, and attaches documentation evidence links. Trigger: /daily-log
---

# /daily-log

Publish daily-log entries to the lab progress issue using
https://github.com/bmw-ece-ntust/daily-log. This skill first **commits & pushes
all lab repos** (the `daily-log-commit` workflow, per repo), then posts the day's
entry — updating the existing daily-plan/log comment in place, or creating a new
one only when none exists.

## Model — Sonnet 5 for the writing, then back (mandatory)

Writing a daily-log is structured-data cross-referencing plus short summary composition:
a routine-workflow task. Opus or Fable spend several times the tokens on it and do not
produce a better entry.

**Claude cannot change its own session model mid-session.** No tool, hook, or setting
does it, so "switch to Sonnet 5 and switch back afterwards" is not literally available
and any skill that claims to do it is lying. The equivalent that IS available, and is
REQUIRED here, is delegation:

- Run the token-heavy work — the Step 0 pending-work scan, and the Step 2 cross-reference
  and entry composition — inside the Sonnet-pinned `project-analyst` sub-agent, or an
  `Agent` call passing `model: "sonnet"`.
- Keep the draft -> confirm -> post loop in the MAIN session, so the human confirmation
  is preserved and nothing reaches the shared issue from a subagent.
- The session returns to its original model by construction, because it never left it.

This is mandatory, not a cost heuristic, and it applies to a single-day entry too: an
exception that depends on first judging an entry "trivial" is an exception that never
fires. If the session is already on Sonnet, do the work inline.

Tell the user once per invocation: *"daily-log composition is delegated to Sonnet 5; this
session stays on <model>."*

## Eligible orgs (hard restriction)

Only repos under **`bmw-ece-ntust`**, **`bmw-ntust-internship`**, and **`raycg`**
(plus slugs listed in `LAB_REPOS` in `lab.config`) count as daily-log progress.
Ignore activity in any other org/account. Set `env.yaml`'s configured orgs to
exactly these three.

Default target issue: `bmw-ece-ntust/progress-plan#366`. Auth: `gh` CLI.

## The day boundary is the clock, 00.00 – 23.59 (hard rule)

A daily-log day is the **calendar day in Asia/Taipei**, from `00.00` to `23.59`. It is
not "the working session", and it does not stretch to wherever the work happened to stop.

**A session that runs past midnight is split at midnight, not carried.** The part before
`24.00` is logged on the day it started; the part from `00.00` onward is logged on the
**next** day, as that day's first bullet. So a session from `21.50` to `00.14` produces
two bullets on two comments:

```markdown
### 2026/09/14
- `21.50 - 23.59` [owner/repo]: <what was done>

### 2026/09/15
- `00.00 - 00.14` [owner/repo]: <the continuation>
```

Never write an end time smaller than the start time, never write `24.30` or `25.00`, and
never leave the after-midnight part off the next day because it looks like a fragment.
The `+1d` end marker that `stm-window.sh` prints means exactly this split is needed — it
is a signal to the composer, not a value to publish.

The same rule decides which comment an interval belongs to when catching up several days
at once: sort by the interval's **start** clock time within its own calendar day.

## Step 0 — Commit & push all lab repos (daily-log-commit sweep)

Before posting, ensure every lab-related local repo has its work committed and
pushed, so the daily-log has commits + LTM records to cross-reference.

1. **Enumerate local repos** (clones under `~/Documents/GitHub` and any other
   known workspace roots):

   ```bash
   for d in "$HOME"/Documents/GitHub/*/.git; do
     r="${d%/.git}"
     url=$(git -C "$r" remote get-url origin 2>/dev/null) || continue
     echo "$r  $url"
   done
   ```

2. **Filter to lab-related repos**: keep a repo only if its `origin` owner is one
   of `bmw-ece-ntust`, `bmw-ntust-internship`, `raycg`, or its `owner/repo` slug
   is listed in `LAB_REPOS` in `lab.config`. Skip everything else silently.

3. **Detect pending work** per kept repo: uncommitted changes
   (`git status --porcelain`) or unpushed commits
   (`git log @{u}..HEAD --oneline`, treat a missing upstream as unpushed).

4. **Run the `daily-log-commit` skill workflow for each repo with pending work**
   (reconcile the 4 project files, commit in SOP `work duration:` format, push,
   write the LTM session record). Repos with nothing pending are skipped —
   report them in one line. If a push fails (auth, diverged branch), report it
   and continue with the remaining repos; do not abort the sweep.

Only after the sweep proceed to posting, so today's commits are visible to the
commit search.

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
     AND metadata->>'owner' IN ('bmw-ece-ntust','bmw-ntust-internship','raycg')
     AND metadata->>'date' >= '<since>'
   GROUP BY 1,2,3 ORDER BY d;
   ```
   (`session`/`activity` rows supplement days without a worklog; `session.doc_url` is a ready evidence link.)

   **Drain offline spools first (mandatory).** Cowork sessions spool to
   `llm-skill-ltm/.ltm-spool/cowork.jsonl` and stay invisible to this query until
   flushed — run `bash "$LTM_HOME/scripts/ltm-sync.sh"` (or at least `ltm-flush.sh`)
   before querying. `pg-memory-conn.sh` falls back to the cached connection string
   (`~/.claude/.pg-memory-conn`, then the termlog cache) when Vault is unreachable,
   so a Vault outage is not a reason to skip the LTM.

   **When the database is unreachable, use STM — it holds the same timestamps.**
   The worklog rows above are DERIVED from local session transcripts, so a Vault,
   tunnel, or Postgres outage does not actually destroy the times: they are still on
   this machine. Read them with no database, no credential, and no network:

   ```bash
   bash "$LTM_HOME/scripts/stm-window.sh" --since <day>
   ```

   **Faster STM entry point: check the top-level repo index first.** Scanning every
   `~/.claude/projects/*/*.jsonl` transcript to find which repos even had activity is
   wasted work when only the times are missing. `stm-index-ingest.sh` (a Stop/SessionEnd
   hook) appends one line per (date, owner, repo, machine) to
   `~/Documents/GitHub/.llm-stm.jsonl` on every session close — a durable, local-only
   backup independent of Postgres. Read it first to narrow which repos to ask about,
   then get that repo's exact times from `stm-window.sh`:

   ```bash
   bash "$LTM_HOME/scripts/llm-stm-index.sh" --since <day>            # which repos
   bash "$LTM_HOME/scripts/stm-window.sh" --repo <owner>/<repo> --since <day>  # that repo's times
   ```

   If the index file doesn't exist yet or is missing a day (e.g. a session predating the
   hook, or a machine where install.sh hasn't run since this was added), fall back to the
   full `stm-window.sh --since <day>` scan above — it is still the source of truth, the
   index is only a cache in front of it.

   **A row tagged with an `llm` other than `claude-code` did not happen in this Claude
   Code install** — it was backed up via `/stm-import` (e.g. ChatGPT, a different
   Claude.ai account). `stm-window.sh` has no transcript for it and will not find it;
   use the `start`/`end` printed directly on that index row instead, and attribute the
   bullet to that `llm`/`account` rather than silently folding it into Claude Code's own
   activity for the day.

   It prints `date, repo, branch, start, end, sessions, sources` — the same shape the
   query above returns — from `~/.claude/projects` transcripts plus every un-flushed
   spool (Cowork, Codex, and this machine's offline queue). An end marked `+1d` ran past
   midnight; `--sessions` gives per-session rows and `--json` machine-readable output.
   Prefer the LTM when it answers, and treat STM as the next rung, never as a shortcut
   past a drain that would have worked.

   **`??:??` is a last resort, not a shortcut.** A placeholder time may be published
   only after all four sources fail for that interval: (1) LTM worklogs *after* the
   spool drain, (2) STM windows from `stm-window.sh`, (3) `termlog.command` windows
   (`min(ts)`/`max(ts)` per repo per day, converted to Asia/Taipei), (4) calendar
   events. A time that exists in any of these MUST be used; never post `??:??` when the
   LTM or STM can supply the value — a database outage is not a source failure,
   because STM is read without the database.

2. **GitHub commits** give the concrete deliverable + the SOP evidence link:

   ```bash
   gh api "repos/<owner>/<repo>/commits?author=<gh-user>&since=<dayT00:00>&until=<dayT23:59>" \
     --jq '.[] | .sha[0:7] + "  " + (.commit.message | split("\n")[0])'
   ```
   Use the 7-digit sha for the evidence link (`.../tree/<7hex>#<section>`).

3. **Verify + compose** as **hourly summary bullets** (see `daily-log.md` Formatting
   Standards): one bullet per interval `` `HH.MM - HH.MM` [owner/repo]: [<achieved
   target>](doc link) ``, linking the **study-notes documentation** at that commit
   (`.../tree/<7hex>#<section>`, resolved via the tool's `--link-to-files`). Never link
   the bare `/commit/<hash>`. Times come from the **worklog**; if a `start` is missing
   there, take the interval from `stm-window.sh`, then from the day's `termlog.command`
   window for that repo; only when no worklog, STM window, termlog, or calendar source
   covers it, write `??:?? - HH.MM` and flag for review.

   **Wording standard — concise, target-first.** The daily-log states *which target was
   achieved* in each interval; the linked study-notes carry the detail. Rules:
   - One line per interval: verb-first, past tense, **≤ 12 words** before the link
     (e.g. `Restructured the SOP into a checklist-first README`).
   - **No sub-bullets.** Never enumerate commits, files, or steps under a bullet — that
     detail lives in the linked study-notes. Several commits toward one target = one
     bullet naming the target, linked to the primary study-notes doc. Two genuinely
     distinct targets in one interval = two bullets sharing the time range, not
     sub-bullets.
   - **Distil, don't copy** commit messages: drop file lists, parentheticals,
     flag/tool names, and markers like `(parallel)` / `(N commits)` — overlapping time
     ranges already show concurrency.
   - **Short-term Goal** = one plain line, the day's main target, ≤ 10 words.
   - **Collapse bulk commits** (e.g. a propagation across N repos) into one bullet, and
     **merge consecutive same-`[owner/repo]` intervals** into one bullet with an
     extended end time (the LTM keeps the detail; the daily-log is the summary).

   LTM-only intervals (no commit) are still logged, flagged as lacking documentation
   evidence; commit-only days are seeded by the tool. A Google Calendar meeting with no
   minutes yet is `[<meeting-title>](minutes documentation header link with 7-digit
   hash)` (placeholder), flagged for review.

4. **Update in place; create only if none.** Look up the day's existing comment
   on the issue (match the `### yyyy/mm/dd` heading) before posting:
   - **Daily-plan comment exists** (posted in the morning via the `daily-plan`
     skill — targets as `- [ ]` checklist items with optional time ticks):
     **edit that comment in place** — convert each achieved target into its
     `hh:mm - hh:mm` duration bullet with an evidence link; keep unachieved
     targets as `- [ ]` with a ` — pending: <reason>` suffix (they roll into the
     next morning's plan).
   - **Daily-log comment exists**: update it in place — fill missing end times,
     add evidence links, append bullets for new sessions/commits not yet listed.
   - **No comment for the day**: create a new daily-log comment in the standard
     format.

   Never leave two comments for one day.

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
