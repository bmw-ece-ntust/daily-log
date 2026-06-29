from __future__ import annotations

import re
from datetime import date

from .github_api import Commit


# Heading like: ### 2026/02/04 (optionally blockquoted: > ### 2026/02/04)
DATE_HEADING_RE = re.compile(
    r"(?im)^\s*(?:>\s*)?(?:#+\s+)(20\d{2})[\/.\-](\d{1,2})[\/.\-](\d{1,2})\b"
)

DAILY_LOGS_START_RE = re.compile(r"(?im)^(?P<quote>\s*(?:>\s*)?)\*\*Daily-logs\*\*:\s*$")

SHORT_TERM_GOAL_RE = re.compile(r"(?im)^(?P<quote>\s*(?:>\s*)?)\*\*Short-term Goal\*\*:\s*$")
SECTION_HEADER_RE = re.compile(r"(?im)^\s*(?:>\s*)?\*\*[^*]+\*\*:\s*$")

BULLET_RE = re.compile(
    r"^(?P<prefix>\s*(?:>\s*)?[-*]\s+)"  # bullet prefix (maybe blockquoted)
    r"(?P<time>`[^`]*`)"  # backticked time range
    r"(?P<tag>(?:\s*\[[^\]]+\])?)"  # optional [owner/repo] project tag
    r"\s*:\s*"  # colon separator
    r"(?P<activity>.+?)\s*$"  # activity tail
)

TIME_SPLIT_RE = re.compile(r"^(?P<start>.*?)\s*-\s*(?P<end>.*)$")

MD_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")

# Fallback: bubble header line like:
# > **GitHub @ijosh-ch** on 2026-02-03 13:08:25 (Taiwan GMT+8):
BUBBLE_ON_DATE_RE = re.compile(r"(?im)^\s*(?:>\s*)?\*\*GitHub\s+@[^*]+\*\*\s+on\s+(20\d{2})-(\d{2})-(\d{2})\b")


def parse_heading_date(body: str) -> date | None:
    text = body or ""

    m = DATE_HEADING_RE.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    m = BUBBLE_ON_DATE_RE.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    return None


def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def similarity_score(activity: str, title: str) -> int:
    a = normalize_text(activity)
    t = normalize_text(title)
    if not a or not t:
        return 0
    if a == t:
        return 100
    if t in a:
        return 80
    if a in t:
        return 70
    return 0


def update_time_range(time_tick: str, end_hhmm: str) -> str:
    raw = time_tick.strip("`")
    m = TIME_SPLIT_RE.match(raw)
    if not m:
        return time_tick

    start = (m.group("start") or "").strip()
    end = (m.group("end") or "").strip()

    if re.search(r"\d", end):
        return time_tick

    if start:
        return f"`{start} - {end_hhmm}`"
    return f"` - {end_hhmm}`"


def link_activity(activity: str, commit: Commit) -> str:
    if MD_LINK_RE.search(activity):
        return activity
    label = activity.strip()
    target = commit.file_url or commit.url
    return f"[{label}]({target})"


def patch_daily_logs(body: str, commits: list[Commit]) -> tuple[str, int]:
    if not body or not commits:
        return body, 0

    lines = body.splitlines()

    start_idx = None
    for i, line in enumerate(lines):
        m = DAILY_LOGS_START_RE.match(line)
        if not m:
            continue
        start_idx = i
        break
    if start_idx is None:
        return body, 0

    changes = 0
    i = start_idx + 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            break

        m = BULLET_RE.match(line)
        if not m:
            i += 1
            continue

        prefix = m.group("prefix")
        time_tick = m.group("time")
        tag = (m.group("tag") or "").strip()
        activity = m.group("activity").strip()

        best = None
        best_score = 0
        for c in commits:
            score = similarity_score(activity, c.title)
            if score > best_score:
                best_score = score
                best = c
            elif score == best_score and score > 0 and best is not None:
                if c.end_hhmm > best.end_hhmm:
                    best = c

        if not best or best_score == 0:
            i += 1
            continue

        if best.short in line or best.sha in line or best.url in line:
            i += 1
            continue

        new_time = update_time_range(time_tick, best.end_hhmm)
        new_activity = link_activity(activity, best)
        # Preserve an existing project tag; otherwise tag with the commit's owner/repo.
        if not tag and best.repo_full_name:
            tag = f"[{best.repo_full_name}]"
        tag_part = f" {tag}" if tag else ""
        new_line = f"{prefix}{new_time}{tag_part}: {new_activity}"

        if new_line != line:
            lines[i] = new_line
            changes += 1

        i += 1

    return "\n".join(lines), changes


def append_unmatched_commits(body: str, commits: list[Commit]) -> tuple[str, int]:
    """Append commits as new bullets under **Daily-logs** if not already referenced."""

    if not body or not commits:
        return body, 0

    # If already present by URL/SHA, don't add.
    existing = set(re.findall(r"https?://github\.com/[^\s)]+", body))
    existing |= set(re.findall(r"\b[0-9a-f]{7,40}\b", body))

    lines = body.splitlines()
    start_idx = None
    quote_prefix = ""
    for i, line in enumerate(lines):
        m = DAILY_LOGS_START_RE.match(line)
        if not m:
            continue
        start_idx = i
        quote_prefix = m.group("quote") or ""
        break
    if start_idx is None:
        return body, 0

    insert_at = start_idx + 1
    # Move past existing bullet lines and any nested text; stop at first blank line.
    while insert_at < len(lines):
        if not lines[insert_at].strip():
            break
        insert_at += 1

    new_lines: list[str] = []
    for c in commits:
        if c.url in existing or c.sha in existing or c.short in existing:
            continue
        target = c.file_url or c.url
        tag = f" [{c.repo_full_name}]" if c.repo_full_name else ""
        new_lines.append(f"{quote_prefix}- ` - {c.end_hhmm}`{tag}: [{c.title}]({target})")

    if not new_lines:
        return body, 0

    # Insert before the blank line terminating the section.
    updated = lines[:insert_at] + new_lines + lines[insert_at:]
    return "\n".join(updated), len(new_lines)


def render_new_day_template(d: date) -> str:
    ds = d.strftime("%Y/%m/%d")
    return (
        f"### {ds}\n\n"
        f"**Short-term Goal**:\n"
        f"<Goal>\n\n"
        f"**Daily-logs**:\n"
        f"- ` - `: <activity>\n"
    )


def render_new_day_from_commits(d: date, commits: list[Commit]) -> str:
    ds = d.strftime("%Y/%m/%d")
    lines = [
        f"### {ds}",
        "",
        "**Short-term Goal**:",
        "<Goal>",
        "",
        "**Daily-logs**:",
    ]
    if not commits:
        lines.append("- ` - `: <activity>")
    else:
        for c in commits:
            target = c.file_url or c.url
            tag = f" [{c.repo_full_name}]" if c.repo_full_name else ""
            lines.append(f"- ` - {c.end_hhmm}`{tag}: [{c.title}]({target})")
    lines.append("")
    return "\n".join(lines)


def render_new_day_from_suggestions(d: date, suggestions: list[str]) -> str:
    ds = d.strftime("%Y/%m/%d")
    lines = [
        f"### {ds}",
        "",
        "**Short-term Goal**:",
        "<Goal>",
        "",
        "**Daily-logs**:",
    ]

    if not suggestions:
        lines.append("- ` - `: <activity>")
    else:
        for s in suggestions:
            lines.append(f"- ` - `: {s}")
    lines.append("")
    return "\n".join(lines)


def patch_short_term_goal(body: str, goal_lines: list[str]) -> tuple[str, int]:
    """Replace the content under **Short-term Goal**: with provided lines.

    Stops replacement at the next blank line or the next section header.
    """

    if not body:
        return body, 0

    lines = body.splitlines()
    idx = None
    quote_prefix = ""
    for i, line in enumerate(lines):
        m = SHORT_TERM_GOAL_RE.match(line)
        if m:
            idx = i
            quote_prefix = m.group("quote") or ""
            break

    if idx is None:
        return body, 0

    start = idx + 1
    end = start
    while end < len(lines):
        if not lines[end].strip():
            break
        if SECTION_HEADER_RE.match(lines[end]):
            break
        end += 1

    new_block = [f"{quote_prefix}{l}" for l in goal_lines]

    updated = lines[:start] + new_block + [""] + lines[end:]
    new_body = "\n".join(updated)
    if new_body == body:
        return body, 0
    return new_body, 1
