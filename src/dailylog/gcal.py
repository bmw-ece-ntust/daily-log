"""Google Calendar integration for daily-log automation."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TAIPEI_TZ = timezone(timedelta(hours=8))


def _get_credentials(credentials_file: str, token_file: str):
    """Load OAuth2 credentials, refreshing or re-authorising as needed."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise ImportError(
            "Google Calendar dependencies not installed.\n"
            "Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        ) from exc

    creds_path = Path(credentials_file).expanduser()
    token_path = Path(token_file).expanduser()

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"Google credentials file not found: {creds_path}\n"
                    "Download from: Google Cloud Console → APIs & Services → "
                    "Credentials → OAuth 2.0 Client IDs → Download JSON"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_calendar_service(credentials_file: str, token_file: str):
    """Return an authenticated Google Calendar API service object."""
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError("Install: pip install google-api-python-client") from exc

    creds = _get_credentials(credentials_file, token_file)
    return build("calendar", "v3", credentials=creds)


def fetch_events(service, calendar_id: str, since: date, until: date) -> list[dict[str, Any]]:
    """Fetch all calendar events in [since, until] (inclusive, Asia/Taipei)."""
    time_min = datetime(since.year, since.month, since.day, tzinfo=TAIPEI_TZ).isoformat()
    time_max = datetime(until.year, until.month, until.day, 23, 59, 59, tzinfo=TAIPEI_TZ).isoformat()

    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500,
        )
        .execute()
    )
    return result.get("items", [])


def event_start_date(event: dict[str, Any]) -> date | None:
    """Return the start date of a calendar event (Asia/Taipei)."""
    start = event.get("start") or {}
    if "dateTime" in start:
        return datetime.fromisoformat(start["dateTime"]).astimezone(TAIPEI_TZ).date()
    if "date" in start:
        return date.fromisoformat(start["date"])
    return None


def is_class_event(event: dict[str, Any], class_keywords: tuple[str, ...] | list[str]) -> bool:
    """Return True if the event title contains a class/lecture keyword."""
    summary = (event.get("summary") or "").lower()
    return any(kw.lower() in summary for kw in class_keywords)


def events_by_day(events: list[dict[str, Any]]) -> dict[date, list[dict[str, Any]]]:
    """Group calendar events by their start date."""
    out: dict[date, list[dict[str, Any]]] = {}
    for ev in events:
        d = event_start_date(ev)
        if d:
            out.setdefault(d, []).append(ev)
    return out


def print_events(events: list[dict[str, Any]], since: date, until: date) -> None:
    """Print a human-readable list of calendar events."""
    print(f"Calendar events {since.isoformat()} → {until.isoformat()}:")
    if not events:
        print("  (none)")
        return
    for ev in events:
        start = event_start_date(ev)
        summary = ev.get("summary") or "(no title)"
        location = ev.get("location") or ""
        loc_str = f"  [{location}]" if location else ""
        print(f"  {start}: {summary}{loc_str}")
