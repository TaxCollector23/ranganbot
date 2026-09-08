"""Deterministic date/time and formatting logic for the workshop schedule.

Deliberately has no dependency on discord.py so it can be unit tested in
isolation. All "current time" logic goes through ``now_pacific()`` so tests
can monkeypatch a single function to control "today".
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import database

PACIFIC = ZoneInfo("America/Los_Angeles")

WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def now_pacific() -> datetime:
    """Current time in Pacific, correctly handling daylight saving time."""
    return datetime.now(PACIFIC)


def today_pacific() -> date:
    return now_pacific().date()


def tomorrow_pacific() -> date:
    return today_pacific() + timedelta(days=1)


def format_time_12h(hhmm: str) -> str:
    """Convert 'HH:MM' 24-hour text to '12:00 PM' style with no leading zero."""
    parsed = datetime.strptime(hhmm, "%H:%M")
    text = parsed.strftime("%I:%M %p")
    return text.lstrip("0") or text


def format_date_header(day: date) -> str:
    return f"{day.strftime('%A, %B')} {day.day}"


def get_workshops_for_date(db_path: str, day: date) -> list[dict]:
    """Look up workshops for a calendar date. Weekends naturally return []."""
    return database.get_workshops_for_day(db_path, day.weekday())


def get_today_schedule(db_path: str) -> tuple[date, list[dict]]:
    day = today_pacific()
    return day, get_workshops_for_date(db_path, day)


def get_tomorrow_schedule(db_path: str) -> tuple[date, list[dict]]:
    day = tomorrow_pacific()
    return day, get_workshops_for_date(db_path, day)


def get_week_schedule(db_path: str) -> dict[int, list[dict]]:
    """Monday(0)..Friday(4) -> list of workshops, in order."""
    return database.get_full_week_schedule(db_path)
