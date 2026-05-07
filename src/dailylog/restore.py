from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .dailylog_md import parse_heading_date


@dataclass(frozen=True)
class BackupComment:
    day: date
    body: str
    created_at: str | None = None
    comment_id: int | None = None


def _flatten_json(obj: Any) -> list[dict[str, Any]]:
    """Return a flat list of comment-like dicts from common GH backup shapes."""

    if obj is None:
        return []

    # Shape A: [{comment}, {comment}, ...]
    if isinstance(obj, list) and (not obj or isinstance(obj[0], dict)):
        return [x for x in obj if isinstance(x, dict)]

    # Shape B: [[{comment}, ...], [{comment}, ...]] (slurped pages)
    if isinstance(obj, list) and obj and isinstance(obj[0], list):
        out: list[dict[str, Any]] = []
        for page in obj:
            if not isinstance(page, list):
                continue
            out.extend([x for x in page if isinstance(x, dict)])
        return out

    # Shape C: {"comments": [...]} or {"items": [...]}
    if isinstance(obj, dict):
        for key in ("comments", "items"):
            val = obj.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]

    return []


def load_backup_comments(path: str | Path) -> list[BackupComment]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    rows = _flatten_json(data)

    out: list[BackupComment] = []
    for r in rows:
        body = str(r.get("body") or "")
        if not body.strip():
            continue
        d = parse_heading_date(body)
        if not d:
            continue
        created_at = r.get("created_at")
        cid = r.get("id")
        out.append(
            BackupComment(
                day=d,
                body=body,
                created_at=str(created_at) if created_at is not None else None,
                comment_id=int(cid) if isinstance(cid, int) else None,
            )
        )

    # Prefer earliest-created comment per day.
    out.sort(key=lambda c: (c.day.isoformat(), c.created_at or ""))
    uniq: dict[date, BackupComment] = {}
    for c in out:
        uniq.setdefault(c.day, c)

    return [uniq[d] for d in sorted(uniq.keys())]


def max_day(comments: Iterable[BackupComment]) -> date | None:
    m: date | None = None
    for c in comments:
        if m is None or c.day > m:
            m = c.day
    return m
