# RanganBot

A small, deterministic Discord bot that answers exactly one question: **what
workshops are on the schedule this week?**

RanganBot has **no AI, no LLM, no MCP, and no general-purpose agent
behavior**. Every response is generated from a fixed schedule stored in
SQLite using plain date/time arithmetic (`zoneinfo` + `datetime`). It exposes
exactly three slash commands and nothing else, and only responds to one
authorized Discord user in one authorized private server.

## What it does

| Command | Behavior |
|---|---|
| `/today` | Shows every workshop scheduled for today (Pacific time). |
| `/tomorrow` | Shows every workshop scheduled for tomorrow (Pacific time). |
| `/schedule` | Shows the full Monday–Friday schedule. |

If a day has no workshop (Monday, or any weekend day), the bot explicitly
replies `No workshop.` instead of an empty response.

All times are `America/Los_Angeles` (Pacific), computed with the IANA
timezone database so daylight saving transitions are handled correctly —
not a hardcoded UTC offset.

## What it deliberately does NOT do

RanganBot cannot and will not:

- Access the LMS, Google Calendar, passwords, or personal files
- Browse the web or fetch arbitrary URLs
- Execute shell commands or arbitrary code from Discord
- Read or write arbitrary files
- Use an LLM, MCP, or any AI model
- Expose an HTTP server or public API
- Accept any command beyond `/today`, `/tomorrow`, and `/schedule`
- Provide any administrative functionality through Discord

The only external service it talks to is Discord's API.

## Project layout

```
ranganbot/
├── bot.py                  # Discord client, slash commands, auth checks
├── database.py              # SQLite schema, seeding, queries
├── schedule.py               # Timezone-aware date logic & formatting (no discord dependency)
├── config.py                 # Environment variable loading/validation
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt        # Runtime + pytest
├── .env.example                # Template for your local .env (never commit .env)
├── .gitignore
├── pytest.ini
├── tests/                        # Unit tests (see "Testing" below)
└── systemd/ranganbot.service       # systemd unit for running on boot
```

---

## Raspberry Pi setup (step by step)

These commands assume Raspberry Pi OS (Debian-based) and a user named `pi`.
Adjust paths/usernames if yours differ.

### 1. Install required system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### 2. Get the code onto the Pi

```bash
cd ~
git clone https://github.com/<your-github-username>/ranganbot.git
cd ranganbot
```

### 3. Create the Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create your `.env` file

```bash
cp .env.example .env
```

### 6. Fill in the Discord bot token, allowed user ID, and allowed server ID

Edit `.env` with your preferred editor:

```bash
nano .env
```

Set the three values (see [Discord setup](#discord-application--bot-setup)
below for how to get them):

```
DISCORD_BOT_TOKEN=<your bot token>
DISCORD_ALLOWED_USER_ID=<your Discord user ID>
DISCORD_ALLOWED_GUILD_ID=<your private server ID>
```

**The bot token is a secret.** Never commit `.env` to Git — it is already
excluded via `.gitignore`.

### 7. Initialize the database

The bot creates and seeds the SQLite database automatically on first
startup, but you can also do it explicitly ahead of time:

```bash
python3 -c "import database, config; database.init_db(config.DATABASE_PATH)"
```

Running this (or starting the bot) multiple times will **not** duplicate
schedule entries — seeding only happens once, tracked internally.

### 8. Run the bot manually for the first test

```bash
python3 bot.py
```

You should see log lines ending with `RanganBot connected as <BotName>#....`
Press `Ctrl+C` to stop it once you've confirmed it connects and `/today`,
`/tomorrow`, and `/schedule` work in your server.

### 9. Install and enable the systemd service

Edit `systemd/ranganbot.service` first if your username or install path
differs from `pi` / `/home/pi/ranganbot`. Then:

```bash
sudo cp systemd/ranganbot.service /etc/systemd/system/ranganbot.service
sudo systemctl daemon-reload
sudo systemctl enable ranganbot.service
sudo systemctl start ranganbot.service
```

This makes RanganBot start automatically on boot and restart automatically
if it ever crashes. No terminal window needs to stay open.

### 10. Check service status

```bash
sudo systemctl status ranganbot.service
```

### 11. View logs

```bash
sudo journalctl -u ranganbot.service -f
```

(Drop `-f` to see history without following live.)

### 12. Restart RanganBot

```bash
sudo systemctl restart ranganbot.service
```

### 13. Updating the bot later

```bash
cd ~/ranganbot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ranganbot.service
```

---

## Discord application / bot setup

You only need to do this once.

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   and click **New Application**. Name it `RanganBot` (or anything you like).
2. In the left sidebar, go to **Bot**. Click **Reset Token** to generate a
   bot token, then copy it — this is the value for `DISCORD_BOT_TOKEN`. Treat
   it like a password.
3. Under **Privileged Gateway Intents**, leave everything **off**.
   RanganBot does not read message content, member lists, or presence data,
   so no privileged intents are required.
4. Go to **OAuth2 → URL Generator**.
   - Under **Scopes**, check `bot` and `applications.commands`.
   - Under **Bot Permissions**, check only:
     - `View Channels`
     - `Send Messages`
   - Do **not** grant `Administrator` or any other permission — the bot
     only needs to see and reply in the channel where you run commands.
5. Copy the generated URL, open it in a browser, and select your **private**
   Discord server as the install target. This invites the bot with the
   minimum permissions.
6. Get your Discord user ID: in Discord, enable **Developer Mode**
   (User Settings → Advanced → Developer Mode), then right-click your own
   name/avatar and choose **Copy User ID**. This is `DISCORD_ALLOWED_USER_ID`.
7. Get your server ID: right-click your private server's icon in the
   sidebar and choose **Copy Server ID**. This is `DISCORD_ALLOWED_GUILD_ID`.
8. Put the token and both IDs into `.env` on the Pi as described in step 6
   of the setup above.

RanganBot registers its slash commands only to the configured server
(guild-scoped sync), so they appear immediately there and are not published
globally to any other server.

---

## Environment variables

| Variable | Meaning |
|---|---|
| `DISCORD_BOT_TOKEN` | Secret bot token from the Developer Portal. Never commit this. |
| `DISCORD_ALLOWED_USER_ID` | Your Discord user ID — the only user the bot will respond to. |
| `DISCORD_ALLOWED_GUILD_ID` | Your private server's ID — the only server the bot will respond in. |

Every interaction is checked against **both** values before any command
runs; anyone else (or any other server) gets a generic rejection message
with no further detail.

---

## Testing

Unit tests cover the schedule data, date/timezone logic, and authorization
checks — no real Discord connection is used or required.

```bash
python3 -m venv .venv        # if not already created
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
```

What's covered:

- Each weekday's workshop count (Monday: none, Tuesday: two, Wednesday/
  Thursday/Friday: one each) and that Zoom URLs are stored exactly as given
- `/today` and `/tomorrow` selecting the correct weekday/date, including
  Sunday→Monday, Friday→Saturday, and Saturday→Sunday transitions
- Weekends returning `No workshop.` for both `/today` and `/tomorrow`
- Pacific timezone handling across the DST boundary (PDT vs. PST offsets)
- Unauthorized users and unauthorized servers being rejected
- Database initialization being idempotent, and a simulated restart not
  duplicating schedule rows

---

## Modifying the schedule later

The schedule lives in the `workshops` table of the SQLite database (default
path: `ranganbot.db` next to `bot.py`, overridable via `RANGANBOT_DB_PATH`).
To change it, either edit the `_SEED_SCHEDULE` list in `database.py` and
delete the existing database file so it reseeds on next startup, or connect
directly with the `sqlite3` CLI and edit rows in place:

```bash
sqlite3 ranganbot.db "SELECT * FROM workshops;"
```

Columns: `day_of_week` (0=Monday..4=Friday), `name`, `start_time`/`end_time`
(24-hour `HH:MM`), `zoom_url`.
