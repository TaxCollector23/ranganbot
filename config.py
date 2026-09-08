"""Configuration loading for RanganBot.

All values come from environment variables (optionally via a local .env
file). Nothing here talks to the network or touches secrets except to read
them into memory -- the token is never logged or printed.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


def _to_int(name: str, value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer Discord snowflake ID, got: {value!r}") from exc


DISCORD_ALLOWED_USER_ID = _to_int("DISCORD_ALLOWED_USER_ID", os.getenv("DISCORD_ALLOWED_USER_ID"))
DISCORD_ALLOWED_GUILD_ID = _to_int("DISCORD_ALLOWED_GUILD_ID", os.getenv("DISCORD_ALLOWED_GUILD_ID"))

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.getenv("RANGANBOT_DB_PATH", os.path.join(_BASE_DIR, "ranganbot.db"))

TIMEZONE_NAME = "America/Los_Angeles"


def validate() -> None:
    """Raise a clear error if required configuration is missing.

    Called explicitly at startup (not at import time) so that this module
    can be imported safely by tests without a real .env file present.
    """
    missing = []
    if not DISCORD_BOT_TOKEN:
        missing.append("DISCORD_BOT_TOKEN")
    if DISCORD_ALLOWED_USER_ID is None:
        missing.append("DISCORD_ALLOWED_USER_ID")
    if DISCORD_ALLOWED_GUILD_ID is None:
        missing.append("DISCORD_ALLOWED_GUILD_ID")
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in the values."
        )
