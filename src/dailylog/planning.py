from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


_HEADING_RE = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+?)\s*$")
_UNCHECKED_RE = re.compile(r"^\s*[-*]\s+\[ \]\s+(?P<item>.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*[-*]\s+(?P<item>.+?)\s*$")


@dataclass(frozen=True)
class SuggestedItem:
    text: str
    source: str
    deadline: date | None = None


_ISO_DATE_RE = re.compile(r"\b(20\d{2})[\-/.](\d{1,2})[\-/.](\d{1,2})\b")
_DUE_RE = re.compile(r"(?i)\b(due|deadline|by)\b\s*[:\-]?\s*(.+)$")
_MDY_RE = re.compile(
    r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:,?\s*(20\d{2}))?\b"
)


def _parse_deadline(s: str, *, today: date) -> date | None:
    s = (s or "").strip()
    if not s:
        return None

    m = _ISO_DATE_RE.search(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    m = _MDY_RE.search(s)
    if m:
        mon = m.group(1).lower()
        day_n = int(m.group(2))
        year_s = m.group(3)
        month_map = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "sept": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        month = month_map.get(mon)
        if not month:
            return None
        year = int(year_s) if year_s else today.year
        try:
            candidate = date(year, month, day_n)
        except ValueError:
            return None
        if not year_s and candidate < today:
            try:
                return date(today.year + 1, month, day_n)
            except ValueError:
                return candidate
        return candidate

    return None


def _normalize_key(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _iter_suggestions_from_text(
    text: str,
    *,
    source: str,
    include_backlog: bool,
    today: date | None = None,
) -> list[SuggestedItem]:
    headings: list[str] = []
    in_backlog = False

    out: list[SuggestedItem] = []
    seen: set[str] = set()

    today = today or date.today()

    for raw_line in (text or "").splitlines():
        line = raw_line.rstrip("\n")

        hm = _HEADING_RE.match(line.strip())
        if hm:
            level = len(hm.group("level"))
            title = hm.group("title").strip()
            if level <= len(headings):
                headings = headings[: level - 1]
            headings.append(title)

            in_backlog = title.lower() == "backlog"
            continue

        m = _UNCHECKED_RE.match(line)
        if m:
            item = m.group("item").strip()
            dl = None
            dm = _DUE_RE.search(item)
            if dm:
                dl = _parse_deadline(dm.group(2), today=today)
            else:
                dl = _parse_deadline(item, today=today)
            ctx = " > ".join(headings[-3:])
            text_out = f"{ctx}: {item}" if ctx else item
            key = _normalize_key(text_out)
            if key and key not in seen:
                out.append(SuggestedItem(text=text_out, source=source, deadline=dl))
                seen.add(key)
            continue

        if include_backlog and in_backlog:
            bm = _BULLET_RE.match(line)
            if not bm:
                continue
            item = bm.group("item").strip()
            dl = None
            dm = _DUE_RE.search(item)
            if dm:
                dl = _parse_deadline(dm.group(2), today=today)
            else:
                dl = _parse_deadline(item, today=today)
            if item.startswith("[ ") or item.startswith("[x") or item.startswith("[X"):
                continue
            if not item or item.startswith("-"):
                continue

            ctx = "Backlog"
            text_out = f"{ctx}: {item}"
            key = _normalize_key(text_out)
            if key and key not in seen:
                out.append(SuggestedItem(text=text_out, source=source, deadline=dl))
                seen.add(key)

    return out


def suggest_from_paths(
    paths: list[str],
    *,
    repo_root: str | Path,
    max_items: int = 6,
    include_backlog: bool = True,
) -> list[SuggestedItem]:
    root = Path(repo_root)
    all_items: list[SuggestedItem] = []
    today = date.today()
    for p in paths:
        fp = (root / p).resolve() if not Path(p).is_absolute() else Path(p)
        if not fp.exists() or not fp.is_file():
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        all_items.extend(_iter_suggestions_from_text(text, source=str(fp), include_backlog=include_backlog, today=today))
        if len(all_items) >= max_items:
            break

    return all_items[:max_items]


def suggest_from_text(
    text: str,
    *,
    source: str,
    max_items: int = 6,
    include_backlog: bool = True,
) -> list[SuggestedItem]:
    today = date.today()
    return _iter_suggestions_from_text(text or "", source=source, include_backlog=include_backlog, today=today)[:max_items]


def rank_suggestions(items: list[SuggestedItem], *, base_day: date) -> list[SuggestedItem]:
    with_deadline = [it for it in items if it.deadline is not None]
    without_deadline = [it for it in items if it.deadline is None]

    with_deadline.sort(key=lambda it: (abs((it.deadline - base_day).days), it.deadline))
    with_deadline.sort(key=lambda it: (0 if it.deadline >= base_day else 1, it.deadline))

    return with_deadline + without_deadline
