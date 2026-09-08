import config
import bot

ALLOWED_USER = 111111111111111111
ALLOWED_GUILD = 222222222222222222
OTHER_USER = 999999999999999999
OTHER_GUILD = 888888888888888888


def _configure(monkeypatch):
    monkeypatch.setattr(config, "DISCORD_ALLOWED_USER_ID", ALLOWED_USER)
    monkeypatch.setattr(config, "DISCORD_ALLOWED_GUILD_ID", ALLOWED_GUILD)


def test_authorized_user_and_guild_accepted(monkeypatch):
    _configure(monkeypatch)
    assert bot.is_authorized(ALLOWED_USER, ALLOWED_GUILD) is True


def test_unauthorized_user_rejected(monkeypatch):
    _configure(monkeypatch)
    assert bot.is_authorized(OTHER_USER, ALLOWED_GUILD) is False


def test_unauthorized_guild_rejected(monkeypatch):
    _configure(monkeypatch)
    assert bot.is_authorized(ALLOWED_USER, OTHER_GUILD) is False


def test_unauthorized_user_and_guild_rejected(monkeypatch):
    _configure(monkeypatch)
    assert bot.is_authorized(OTHER_USER, OTHER_GUILD) is False


def test_missing_guild_id_rejected(monkeypatch):
    """Direct messages / non-guild interactions have no guild_id."""
    _configure(monkeypatch)
    assert bot.is_authorized(ALLOWED_USER, None) is False


def test_missing_user_id_rejected(monkeypatch):
    _configure(monkeypatch)
    assert bot.is_authorized(None, ALLOWED_GUILD) is False
