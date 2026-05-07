"""Generate reminder.md: missing daily-log dates and activities lacking evidence links."""
from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# Matches a Markdown hyperlink: [text](url)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")

# Matches a Daily-logs bullet line (may be blockquoted)
BULLET_RE = re.compile(
    r"^(?:\s*(?:>\s*)?[-*]\s+)"
    r"(?P<time>`[^`]*`)"
    r"\s*:\s*"
    r"(?P<activity>.+?)\s*$"
)

# Keywords in the time-tick or activity that mark a special (no-evidence) entry
_SKIP_KEYWORDS = frozenset({"sick leave", "holiday", "absent", "time replacement", "leave"})


def _has_evidence(activity: str) -> bool:
    return bool(MD_LINK_RE.search(activity))


def _is_special_entry(time_tick: str, activity: str) -> bool:
    combined = (time_tick + " " + activity).lower()
    return any(kw in combined for kw in _SKIP_KEYWORDS)


def _is_class_activity(
    activity: str,
    day_events: list[dict[str, Any]],
    class_keywords: tuple[str, ...] | list[str],
) -> bool:
    """Return True if the activity is a class/lecture (no evidence required)."""
    activity_lower = activity.lower()
    # Check activity text itself
    if any(kw.lower() in activity_lower for kw in class_keywords):
        return True
    # Cross-reference with calendar events: if the activity name appears in an event
    # that is tagged as a class, we skip it.
    for ev in day_events:
        ev_summary = (ev.get("summary") or "").lower()
        if not any(kw.lower() in ev_summary for kw in class_keywords):
            continue
        # Rough match: any word >3 chars from the event title appears in the activity
        ev_words = {w for w in re.split(r"\W+", ev_summary) if len(w) > 3}
        if any(w in activity_lower for w in ev_words):
            return True
    return False


def get_missing_dates(since: date, until: date, existing_days: set[date], skip_weekends: bool = True) -> list[date]:
    """Return weekdays in [since, until] that have no daily-log comment."""
    missing: list[date] = []
    cur = since
    while cur <= until:
        if skip_weekends and cur.weekday() >= 5:
            cur += timedelta(days=1)
            continue
        if cur not in existing_days:
            missing.append(cur)
        cur += timedelta(days=1)
    return missing


def get_activities_without_evidence(
    comments: list[dict[str, Any]],
    cal_events_by_day: dict[date, list[dict[str, Any]]],
    class_keywords: tuple[str, ...] | list[str],
) -> list[tuple[date, str]]:
    """Return (date, activity_text) pairs for bullets that lack a hyperlink.

    Skips: special entries (SICK LEAVE, HOLIDAY, ABSENT), class/lecture events.
    """
    from .dailylog_md import DAILY_LOGS_START_RE, parse_heading_date

    results: list[tuple[date, str]] = []

    for comment in comments:
        body = comment.get("body") or ""
        d = parse_heading_date(body)
        if not d:
            continue

        day_events = cal_events_by_day.get(d) or []
        lines = body.splitlines()
        in_daily_logs = False

        for line in lines:
            if DAILY_LOGS_START_RE.match(line):
                in_daily_logs = True
                continue
            if not in_daily_logs:
                continue
            if not line.strip():
                break

            m = BULLET_RE.match(line)
            if not m:
                continue

            time_tick = m.group("time")
            activity = m.group("activity").strip()

            if _is_special_entry(time_tick, activity):
                continue
            if _has_evidence(activity):
                continue
            if _is_class_activity(activity, day_events, class_keywords):
                continue

            results.append((d, activity))

    return sorted(results, key=lambda x: x[0])


def generate_reminder(
    missing_dates: list[date],
    activities_without_evidence: list[tuple[date, str]],
    output_path: str | Path,
) -> None:
    """Write reminder.md summarising what needs attention."""
    lines: list[str] = ["# Daily-Log Reminder", ""]

    # Section 1: Missing dates
    lines.append("## Missing Daily-Log Entries")
    lines.append("")
    if missing_dates:
        for d in missing_dates:
            lines.append(f"- `{d.isoformat()}` ({d.strftime('%A')})")
    else:
        lines.append("_No missing entries — all working days are covered._")
    lines.append("")

    # Section 2: Activities without evidence
    lines.append("## Activities Without Evidence")
    lines.append("")
    if activities_without_evidence:
        lines.append(
            "> Each activity below has no hyperlink. Attach a commit link, PR link, "
            "or other evidence (specific file URL preferred — see format below).\n"
            "> Class/lecture events detected from Google Calendar are excluded automatically."
        )
        lines.append("")
        lines.append("**Link format** (preferred):")
        lines.append("```")
        lines.append("[Description](https://github.com/org/repo/blob/abc1234/path/to/file.md#section)")
        lines.append("```")
        lines.append("")
        current_day: date | None = None
        for d, activity in activities_without_evidence:
            if d != current_day:
                current_day = d
                lines.append(f"### {d.isoformat()} ({d.strftime('%A')})")
                lines.append("")
            lines.append(f"- {activity}")
        lines.append("")
    else:
        lines.append("_All activities have evidence. Well done!_")
        lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output_path}")
