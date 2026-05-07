from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ContributionSourcesConfig:
    orgs: tuple[str, ...]
    repo_owners: tuple[str, ...]
    repos: tuple[str, ...]


@dataclass(frozen=True)
class GitHubConfig:
    login: str
    contribution_sources: ContributionSourcesConfig
    repo_owner: str
    repo_name: str
    issue_number: int
    timezone: str = "Asia/Taipei"
    seed_new_day_from_commits: bool = False
    append_unmatched_commits: bool = True


@dataclass(frozen=True)
class ScheduleConfig:
    times: tuple[str, ...]


@dataclass(frozen=True)
class TimelineConfig:
    lookback_days: int = 14
    start_date: str = "2023-09-01"


@dataclass(frozen=True)
class GoogleCalendarConfig:
    enabled: bool = False
    credentials_file: str = "~/.config/dailylog/credentials.json"
    token_file: str = "~/.config/dailylog/token.json"
    calendar_id: str = "primary"
    class_keywords: tuple[str, ...] = ("class", "lecture", "seminar", "course", "tutorial")


@dataclass(frozen=True)
class ReminderConfig:
    output_path: str = "reminder.md"


@dataclass(frozen=True)
class OverleafProject:
    name: str
    repo_path: str


@dataclass(frozen=True)
class OverleafConfig:
    enabled: bool
    projects: tuple[OverleafProject, ...]


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool
    provider: str
    base_url: str
    model: str
    api_key_env: str


@dataclass(frozen=True)
class PlanningConfig:
    enabled: bool
    sources: tuple[str, ...]
    max_suggestions: int = 6
    include_backlog: bool = True


@dataclass(frozen=True)
class AppConfig:
    github: GitHubConfig
    schedule: ScheduleConfig
    timeline: TimelineConfig
    google_calendar: GoogleCalendarConfig
    reminder: ReminderConfig
    overleaf: OverleafConfig
    llm: LLMConfig
    planning: PlanningConfig


def _require(d: dict[str, Any], key: str) -> Any:
    if key not in d:
        raise KeyError(f"Missing required config key: {key}")
    return d[key]


def load_config(path: str | Path) -> AppConfig:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    gh = _require(data, "github")
    schedule = data.get("schedule") or {}
    overleaf = data.get("overleaf") or {}
    llm = data.get("llm") or {}
    planning = data.get("planning") or {}
    timeline_raw = data.get("timeline") or {}
    gcal_raw = data.get("google_calendar") or {}
    reminder_raw = data.get("reminder") or {}

    # Contribution sources: support both new `contribution_sources:` and old single `org:`.
    sources_raw = gh.get("contribution_sources") or {}
    if not sources_raw and gh.get("org"):
        sources_raw = {"orgs": [gh["org"]], "repo_owners": [], "repos": []}

    sources_cfg = ContributionSourcesConfig(
        orgs=tuple(sources_raw.get("orgs") or []),
        repo_owners=tuple(sources_raw.get("repo_owners") or []),
        repos=tuple(sources_raw.get("repos") or []),
    )

    github_cfg = GitHubConfig(
        login=str(_require(gh, "login")),
        contribution_sources=sources_cfg,
        repo_owner=str(_require(gh, "repo_owner")),
        repo_name=str(_require(gh, "repo_name")),
        issue_number=int(_require(gh, "issue_number")),
        timezone=str(gh.get("timezone") or "Asia/Taipei"),
        seed_new_day_from_commits=bool(gh.get("seed_new_day_from_commits") or False),
        append_unmatched_commits=bool(
            gh.get("append_unmatched_commits") if "append_unmatched_commits" in gh else True
        ),
    )

    schedule_cfg = ScheduleConfig(times=tuple(schedule.get("times") or []))

    timeline_cfg = TimelineConfig(
        lookback_days=int(timeline_raw.get("lookback_days") or 14),
        start_date=str(timeline_raw.get("start_date") or "2023-09-01"),
    )

    gcal_cfg = GoogleCalendarConfig(
        enabled=bool(gcal_raw.get("enabled") or False),
        credentials_file=str(gcal_raw.get("credentials_file") or "~/.config/dailylog/credentials.json"),
        token_file=str(gcal_raw.get("token_file") or "~/.config/dailylog/token.json"),
        calendar_id=str(gcal_raw.get("calendar_id") or "primary"),
        class_keywords=tuple(gcal_raw.get("class_keywords") or ["class", "lecture", "seminar", "course", "tutorial"]),
    )

    reminder_cfg = ReminderConfig(
        output_path=str(reminder_raw.get("output_path") or "reminder.md"),
    )

    projects = []
    for prj in overleaf.get("projects") or []:
        projects.append(OverleafProject(name=str(_require(prj, "name")), repo_path=str(_require(prj, "repo_path"))))
    overleaf_cfg = OverleafConfig(enabled=bool(overleaf.get("enabled") or False), projects=tuple(projects))

    llm_cfg = LLMConfig(
        enabled=bool(llm.get("enabled") or False),
        provider=str(llm.get("provider") or "openai_compatible"),
        base_url=str(llm.get("base_url") or ""),
        model=str(llm.get("model") or ""),
        api_key_env=str(llm.get("api_key_env") or "LLM_API_KEY"),
    )

    planning_cfg = PlanningConfig(
        enabled=bool(planning.get("enabled") or False),
        sources=tuple(planning.get("sources") or ["README.md", "daily-logs/2025-daily-log.md"]),
        max_suggestions=int(planning.get("max_suggestions") or 6),
        include_backlog=bool(planning.get("include_backlog") if "include_backlog" in planning else True),
    )

    return AppConfig(
        github=github_cfg,
        schedule=schedule_cfg,
        timeline=timeline_cfg,
        google_calendar=gcal_cfg,
        reminder=reminder_cfg,
        overleaf=overleaf_cfg,
        llm=llm_cfg,
        planning=planning_cfg,
    )
