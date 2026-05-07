from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

TAIPEI_TZ = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class OverleafCommit:
    sha: str
    short: str
    dt: datetime
    title: str


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def _parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def list_commits(repo_path: str, since: date, until: date) -> list[OverleafCommit]:
    cmd = [
        "git",
        "-C",
        repo_path,
        "log",
        f"--since={since.isoformat()}T00:00:00",
        f"--until={until.isoformat()}T23:59:59",
        "--pretty=format:%H\t%aI\t%s",
    ]
    proc = _run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"git log failed for {repo_path}")

    commits: list[OverleafCommit] = []
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        sha, when, title = parts
        dt = _parse_iso(when).astimezone(TAIPEI_TZ)
        commits.append(OverleafCommit(sha=sha, short=sha[:7], dt=dt, title=title.strip()))

    return commits


def summarize_by_day(commits: list[OverleafCommit]) -> dict[date, list[OverleafCommit]]:
    out: dict[date, list[OverleafCommit]] = {}
    for c in commits:
        out.setdefault(c.dt.date(), []).append(c)
    for d, cs in out.items():
        cs.sort(key=lambda c: c.dt)
    return out


def render_summary_markdown(project_name: str, day: date, commits: list[OverleafCommit]) -> str:
    if not commits:
        return f"**Overleaf ({project_name})**: no activity\n"

    lines = [f"**Overleaf ({project_name})**:"]
    for c in commits:
        lines.append(f"- {c.dt.strftime('%H:%M')} {c.short} {c.title}")
    return "\n".join(lines) + "\n"
