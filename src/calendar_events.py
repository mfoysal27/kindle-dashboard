"""
Google Calendar fetching via the 'Secret address in iCal format'.

Recurring events (weekly meetings, etc.) are stored once in the feed with an
RRULE. We use `recurring-ical-events` to expand them into concrete dated
occurrences inside our lookahead window, so they show up correctly.

As with weather, failures degrade gracefully into {"ok": False, ...}.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

try:
    import icalendar
    import recurring_ical_events
except ImportError:  # keeps local linting friendly before `pip install`
    icalendar = None
    recurring_ical_events = None

TIMEOUT = 20  # seconds


def fetch_events(config) -> dict:
    """
    Return {"ok": True, "events": [ {...}, ... ]} where each event is:
      {"start": datetime, "all_day": bool, "summary": str}
    sorted by start time, limited to config.MAX_EVENTS.
    On failure: {"ok": False, "error": "..."}.
    """
    url = config.get_ical_url()
    if not url:
        return {"ok": False, "error": "ICAL_URL not set"}
    if recurring_ical_events is None:
        return {"ok": False, "error": "recurring-ical-events not installed"}

    tz = ZoneInfo(config.TIMEZONE)

    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        cal = icalendar.Calendar.from_ical(resp.text)

        # Expand recurring events across our window.
        now = datetime.now(tz)
        end = now + timedelta(days=config.LOOKAHEAD_DAYS)
        occurrences = recurring_ical_events.of(cal).between(now, end)

        events = [_normalise(ev, tz) for ev in occurrences]
        events = [e for e in events if e is not None]
        events.sort(key=lambda e: e["sort_key"])

        return {"ok": True, "events": events[: config.MAX_EVENTS]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def _normalise(ev, tz) -> dict | None:
    """Convert a raw iCal event into our simple dict, in local time."""
    try:
        summary = str(ev.get("SUMMARY", "(no title)"))
        dtstart = ev.get("DTSTART").dt

        # All-day events are plain `date` objects, not `datetime`.
        if isinstance(dtstart, datetime):
            start_local = dtstart.astimezone(tz)
            all_day = False
            sort_key = start_local
        else:
            # date -> treat as local midnight for ordering.
            start_local = datetime(dtstart.year, dtstart.month, dtstart.day, tzinfo=tz)
            all_day = True
            sort_key = start_local

        return {
            "start": start_local,
            "all_day": all_day,
            "summary": summary,
            "sort_key": sort_key,
        }
    except Exception:  # noqa: BLE001 - skip any malformed event
        return None
