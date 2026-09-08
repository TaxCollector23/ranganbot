"""RanganBot: a small, deterministic Discord bot for a weekly workshop schedule.

No AI, no LLM, no MCP, no general-purpose agent behavior. Every response is
generated from a fixed SQLite schedule using plain date/time arithmetic.
Only three slash commands exist: /today, /tomorrow, /schedule.
"""

import logging
import sys

import discord
from discord import app_commands

import config
import database
import schedule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ranganbot")

# Silence discord.py's own verbose debug/info noise a bit while keeping warnings/errors.
logging.getLogger("discord").setLevel(logging.WARNING)

REJECTION_MESSAGE = "This bot is not available to you."


def is_authorized(user_id: int, guild_id: int | None) -> bool:
    """Pure, testable authorization check.

    Both the calling user and the originating server must match the
    configured values. Deliberately returns a single boolean with no
    detail about *which* check failed, so callers can give a uniform
    rejection message that leaks no information to unauthorized callers.
    """
    if guild_id is None or guild_id != config.DISCORD_ALLOWED_GUILD_ID:
        return False
    if user_id is None or user_id != config.DISCORD_ALLOWED_USER_ID:
        return False
    return True


def build_day_embed(title: str, day, workshops: list[dict]) -> discord.Embed:
    header = f"\U0001f4c5 {schedule.format_date_header(day)}"
    embed = discord.Embed(title=header, color=discord.Color.blurple())
    if not workshops:
        embed.description = "No workshop."
        return embed
    for workshop in workshops:
        start = schedule.format_time_12h(workshop["start_time"])
        end = schedule.format_time_12h(workshop["end_time"])
        value = f"{start}–{end} Pacific"
        if workshop.get("zoom_url"):
            value += f"\n[Join Zoom]({workshop['zoom_url']})"
        embed.add_field(name=workshop["name"], value=value, inline=False)
    return embed


def build_week_embed(week_schedule: dict[int, list[dict]]) -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f4c5 Weekly Workshop Schedule",
        color=discord.Color.blurple(),
    )
    for day_index in range(5):
        day_name = schedule.WEEKDAY_NAMES[day_index]
        workshops = week_schedule.get(day_index, [])
        if not workshops:
            value = "No workshop."
        else:
            lines = []
            for workshop in workshops:
                start = schedule.format_time_12h(workshop["start_time"])
                end = schedule.format_time_12h(workshop["end_time"])
                line = f"**{workshop['name']}**\n{start}–{end} Pacific"
                if workshop.get("zoom_url"):
                    line += f"\n[Join Zoom]({workshop['zoom_url']})"
                lines.append(line)
            value = "\n\n".join(lines)
        embed.add_field(name=day_name, value=value, inline=False)
    return embed


class RanganBotTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id if interaction.user else None
        if is_authorized(user_id, interaction.guild_id):
            return True
        log.warning("Rejected unauthorized interaction (user_id/guild_id withheld from logs).")
        if not interaction.response.is_done():
            await interaction.response.send_message(REJECTION_MESSAGE, ephemeral=True)
        return False

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        log.exception("Unhandled error while processing a command: %s", error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "Something went wrong handling that command.", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Something went wrong handling that command.", ephemeral=True
                )
        except discord.HTTPException:
            log.exception("Failed to send error response to Discord.")


class RanganBotClient(discord.Client):
    def __init__(self):
        # Slash-command interactions are delivered regardless of intent
        # flags, and this bot never reads message content, member lists,
        # or presence data, so nearly everything stays off. `guilds` is
        # the one exception: it is not a privileged intent (no Developer
        # Portal toggle required) and keeps discord.py's internal guild
        # cache consistent.
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(intents=intents)
        self.tree = RanganBotTree(self)

    async def setup_hook(self) -> None:
        database.init_db(config.DATABASE_PATH)
        guild = discord.Object(id=config.DISCORD_ALLOWED_GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        try:
            await self.tree.sync(guild=guild)
        except discord.HTTPException:
            # Do not let a sync failure (e.g. the bot has not been invited
            # to the configured guild yet, or a transient API error) take
            # down the whole connection -- the bot should still come
            # online so the problem can be diagnosed and fixed.
            log.exception(
                "Failed to sync slash commands to the configured guild; "
                "the bot will still connect, but commands may not appear "
                "until this is resolved (check DISCORD_ALLOWED_GUILD_ID and "
                "that the bot has been invited to that server)."
            )
        else:
            log.info("Slash commands synced to the configured guild.")

    async def on_ready(self) -> None:
        log.info("RanganBot connected as %s.", self.user)

    async def on_disconnect(self) -> None:
        log.warning("Disconnected from Discord; the client will attempt to reconnect.")

    async def on_resumed(self) -> None:
        log.info("Discord session resumed.")


client = RanganBotClient()
tree = client.tree


@tree.command(name="today", description="Show every workshop scheduled for today.")
async def today_command(interaction: discord.Interaction) -> None:
    day, workshops = schedule.get_today_schedule(config.DATABASE_PATH)
    embed = build_day_embed("Today", day, workshops)
    await interaction.response.send_message(embed=embed)


@tree.command(name="tomorrow", description="Show every workshop scheduled for tomorrow.")
async def tomorrow_command(interaction: discord.Interaction) -> None:
    day, workshops = schedule.get_tomorrow_schedule(config.DATABASE_PATH)
    embed = build_day_embed("Tomorrow", day, workshops)
    await interaction.response.send_message(embed=embed)


@tree.command(name="schedule", description="Show the complete Monday-Friday workshop schedule.")
async def schedule_command(interaction: discord.Interaction) -> None:
    week = schedule.get_week_schedule(config.DATABASE_PATH)
    embed = build_week_embed(week)
    await interaction.response.send_message(embed=embed)


def main() -> None:
    try:
        config.validate()
    except RuntimeError as exc:
        log.error(str(exc))
        sys.exit(1)

    database.init_db(config.DATABASE_PATH)

    try:
        # discord.py's Client.run() already reconnects automatically on
        # transient network/gateway drops; this try/except only covers a
        # fatal startup failure (e.g. bad token), which systemd will retry
        # at the process level per Restart=on-failure.
        client.run(config.DISCORD_BOT_TOKEN, log_handler=None)
    except discord.LoginFailure:
        log.error("Login failed: the Discord bot token is invalid.")
        sys.exit(1)
    except Exception:
        log.exception("RanganBot exited due to an unexpected error.")
        sys.exit(1)


if __name__ == "__main__":
    main()
