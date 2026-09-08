"""SQLite persistence for the RanganBot workshop schedule.

The schedule is fixed content (workshop names, times, Zoom links) but is
stored in SQLite -- rather than hardcoded in the bot logic -- so it is easy
to inspect and modify later without touching Python code.

Day-of-week convention: 0 = Monday ... 4 = Friday (matches
``datetime.date.weekday()``). Saturday (5) and Sunday (6) intentionally have
no rows, since the workshop schedule never runs on weekends.
"""

import sqlite3
from contextlib import closing

_SEED_FLAG_KEY = "seeded_v1"

# (day_of_week, name, start_time "HH:MM" 24h, end_time "HH:MM" 24h, zoom_url)
_SEED_SCHEDULE = [
    (1, "Honors Geometry", "10:00", "11:00", "https://springeducationgroup.zoom.us/j/91759775467"),
    (1, "MS Spanish 2", "13:00", "14:00",
     "https://springeducationgroup.zoom.us/j/5705096276?pwd=E7sXftivTwju2VaaFn9P7qLbBRPD70.1"),
    (2, "8th Grade Science", "08:00", "09:00",
     "https://springeducationgroup.zoom.us/j/92352719778?pwd=a1psd0xWYytVMzBNaklRb0wvVllBUT09"),
    (3, "Adv 8th Grade English", "10:00", "11:00", "https://springeducationgroup.zoom.us/my/eweaverlss"),
    (4, "Adv US History", "11:00", "12:00", "https://springeducationgroup.zoom.us/my/rwozniak1"),
]


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    """Create tables if needed and seed the schedule exactly once.

    Safe to call on every startup: subsequent calls are no-ops for the
    schedule data because a "seeded" flag is recorded in the meta table.
    """
    with closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workshops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                    name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    zoom_url TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

            already_seeded = conn.execute(
                "SELECT 1 FROM meta WHERE key = ?", (_SEED_FLAG_KEY,)
            ).fetchone()

            if not already_seeded:
                conn.executemany(
                    """
                    INSERT INTO workshops (day_of_week, name, start_time, end_time, zoom_url)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    _SEED_SCHEDULE,
                )
                conn.execute(
                    "INSERT INTO meta (key, value) VALUES (?, ?)", (_SEED_FLAG_KEY, "1")
                )


def get_workshops_for_day(db_path: str, day_of_week: int) -> list[dict]:
    """Return workshops for the given weekday (0=Monday..6=Sunday), sorted by start time."""
    with closing(get_connection(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT name, start_time, end_time, zoom_url
            FROM workshops
            WHERE day_of_week = ?
            ORDER BY start_time ASC
            """,
            (day_of_week,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_full_week_schedule(db_path: str) -> dict[int, list[dict]]:
    """Return a mapping of weekday index (0=Monday..4=Friday) to workshop list."""
    with closing(get_connection(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT day_of_week, name, start_time, end_time, zoom_url
            FROM workshops
            WHERE day_of_week BETWEEN 0 AND 4
            ORDER BY day_of_week ASC, start_time ASC
            """
        ).fetchall()

    schedule: dict[int, list[dict]] = {day: [] for day in range(5)}
    for row in rows:
        schedule[row["day_of_week"]].append(
            {
                "name": row["name"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "zoom_url": row["zoom_url"],
            }
        )
    return schedule
