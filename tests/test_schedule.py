from datetime import date, datetime
from zoneinfo import ZoneInfo

import database
import schedule


def _seeded_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    return db_path


def test_today_selects_correct_weekday_tuesday(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    tuesday = date(2026, 9, 8)  # a real Tuesday
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 8, 9, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_today_schedule(db_path)

    assert day == tuesday
    assert len(workshops) == 2


def test_today_selects_correct_weekday_monday(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 14, 9, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_today_schedule(db_path)

    assert day.weekday() == 0  # Monday
    assert workshops == []


def test_tomorrow_calculates_correct_date(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    # Tuesday Sept 8, 2026 -> tomorrow is Wednesday Sept 9, 2026
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 8, 22, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_tomorrow_schedule(db_path)

    assert day == date(2026, 9, 9)
    assert len(workshops) == 1
    assert workshops[0]["name"] == "8th Grade Science"


def test_friday_to_saturday_tomorrow_has_no_workshop(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    # Friday Sept 11, 2026 -> tomorrow is Saturday Sept 12, 2026
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 11, 12, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_tomorrow_schedule(db_path)

    assert day == date(2026, 9, 12)
    assert day.weekday() == 5  # Saturday
    assert workshops == []


def test_saturday_returns_no_workshop(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 12, 12, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_today_schedule(db_path)

    assert day.weekday() == 5
    assert workshops == []


def test_sunday_returns_no_workshop(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 13, 12, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_today_schedule(db_path)

    assert day.weekday() == 6
    assert workshops == []


def test_sunday_to_monday_tomorrow(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    # Sunday Sept 13, 2026 -> tomorrow is Monday Sept 14, 2026 (no workshop, but correct date)
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 13, 12, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_tomorrow_schedule(db_path)

    assert day == date(2026, 9, 14)
    assert day.weekday() == 0
    assert workshops == []


def test_saturday_to_sunday_tomorrow(tmp_path, monkeypatch):
    db_path = _seeded_db(tmp_path)
    monkeypatch.setattr(schedule, "now_pacific", lambda: datetime(2026, 9, 12, 12, 0, tzinfo=schedule.PACIFIC))

    day, workshops = schedule.get_tomorrow_schedule(db_path)

    assert day == date(2026, 9, 13)
    assert day.weekday() == 6
    assert workshops == []


def test_pacific_timezone_handles_dst_summer_offset():
    # Mid-July is Pacific Daylight Time: UTC-7
    summer = datetime(2026, 7, 15, 12, 0, tzinfo=schedule.PACIFIC)
    assert summer.utcoffset().total_seconds() / 3600 == -7


def test_pacific_timezone_handles_standard_winter_offset():
    # Mid-January is Pacific Standard Time: UTC-8
    winter = datetime(2026, 1, 15, 12, 0, tzinfo=schedule.PACIFIC)
    assert winter.utcoffset().total_seconds() / 3600 == -8


def test_pacific_date_derived_correctly_near_utc_midnight_boundary(monkeypatch):
    """A moment that is one calendar date in UTC but still the previous
    calendar date in Pacific must resolve to the Pacific date."""
    # 2026-09-09 05:30 UTC is 2026-09-08 22:30 Pacific (PDT, UTC-7)
    utc_moment = datetime(2026, 9, 9, 5, 30, tzinfo=ZoneInfo("UTC"))
    monkeypatch.setattr(schedule, "now_pacific", lambda: utc_moment.astimezone(schedule.PACIFIC))

    assert schedule.today_pacific() == date(2026, 9, 8)


def test_format_time_12h():
    assert schedule.format_time_12h("10:00") == "10:00 AM"
    assert schedule.format_time_12h("13:00") == "1:00 PM"
    assert schedule.format_time_12h("00:00") == "12:00 AM"
    assert schedule.format_time_12h("12:00") == "12:00 PM"


def test_format_date_header():
    assert schedule.format_date_header(date(2026, 9, 8)) == "Tuesday, September 8"
