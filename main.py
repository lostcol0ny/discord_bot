import os
import sys
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pytz # type: ignore
import discord  # type: ignore
from discord import app_commands  # type: ignore
from dotenv import load_dotenv  # type: ignore
from blizzardapi2 import BlizzardApi  # type: ignore

# Constants
AUTHOR_ICON_IMAGE: str = "https://i.imgur.com/is26wrA.jpeg"
TWW_IMAGE_URL: str = "https://i.imgur.com/jJnPkKA.png"
COLOR_GREEN: int = 0x00FF00
COLOR_RED: int = 0xFF0000
DEFAULT_REALM_ID: int = 57

# Configuration
load_dotenv()


def get_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable {key} is not set")
    return value


class Config:
    BOT_SECRET_KEY: str = get_env("BOT_SECRET_KEY")
    BNET_CLIENT_ID: str = get_env("BNET_CLIENT_ID")
    BNET_CLIENT_SECRET: str = get_env("BNET_CLIENT_SECRET")


config = Config()

# Logging setup
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Discord setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Blizzard API setup
blizzard_api = BlizzardApi(config.BNET_CLIENT_ID, config.BNET_CLIENT_SECRET)


# Error handler
@tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"An error occurred: {str(error)}", ephemeral=True
        )

    logging.error(f"Error in {interaction.command.name}: {str(error)}")


# Commands
@tree.command(name="ping", description="Is the bot responding?")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        f"Pong! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ephemeral=True
    )
    logging.info(
        f"Ping command used by {interaction.user.name} ({interaction.user.id})"
    )


@tree.command(name="tww", description="Countdown to The War Within")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.channel.id))
async def tww(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    try:
        # Timezones, man
        cst = pytz.timezone("America/Chicago")
        now = datetime.now(cst)
        
        # 5 PM on respective days
        tww_season1_start = cst.localize(datetime(2024, 9, 12, 10, 0, 0))
        tww_mplus = cst.localize(datetime(2024, 9, 17, 12, 0, 0))
        tww_wing3 = cst.localize(datetime(2024, 9, 24, 12, 0, 0))

        def format_timedelta(delta):
            return f"{delta.days} days, {delta.seconds // 3600} hours, {delta.seconds // 60 % 60} minutes, {delta.seconds % 60} seconds"

        embed = discord.Embed(description="", color=COLOR_GREEN)
        embed.set_author(name="Countdown to The War Within", icon_url=AUTHOR_ICON_IMAGE)
        embed.set_image(url=TWW_IMAGE_URL)
        embed.add_field(
            name="Season 1 Starts (9/10): Raid Finder Wing 1, Heroic Nerub-at Palace, Mythic 0, World Bosses, Heroic Seasonal Dungeons",
            value=format_timedelta(tww_season1_start - now) if tww_season1_start > now else "It's released! Go play!",
            inline=True,
        )
        embed.add_field(
            name="9/17: Mythic Nerub-ar Palace, Raid Finder Wing 2, Story Difficulty for Nerub-ar Palace, M+ Available",
            value=format_timedelta(tww_mplus - now) if tww_mplus > now else "Go grind!",
            inline=True,
        )
        embed.add_field(
            name="9/24: Raid Finder Wing 3",
            value=format_timedelta(tww_wing3 - now) if tww_wing3 > now else "Go grind!",
            inline=True,
        )

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in TWW command: {str(e)}")


@tree.command(name="token", description="Get the current WoW token value")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.channel.id))
async def token(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    try:
        token_obj = blizzard_api.wow.game_data.get_token_index("us", "en_US")

        price: int = token_obj["price"]
        time: int = token_obj["last_updated_timestamp"] // 1000

        formatted_price = f"**{price // 10000:,}** gold"
        formatted_time = datetime.fromtimestamp(time).strftime("%c")

        embed = discord.Embed(description=formatted_price, color=COLOR_GREEN)
        embed.set_author(name="Current Token Price", icon_url=AUTHOR_ICON_IMAGE)
        embed.set_footer(text=f"As of {formatted_time}")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in token command: {str(e)}\n{token_obj}")


@tree.command(name="realm", description="Get the current WoW realm status")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.channel.id))
async def realm(
    interaction: discord.Interaction, realm_id: int = DEFAULT_REALM_ID
) -> None:
    await interaction.response.defer()
    try:
        realm_obj = blizzard_api.wow.game_data.get_connected_realm(
            "us", "en_US", realm_id
        )
        
        realm_name = realm_obj["realms"][0]["name"]
        realm_status = realm_obj["status"]["name"]
        realm_queue = realm_obj["has_queue"]
        realm_population = realm_obj["population"]["name"]

        color = COLOR_GREEN if realm_status == "Up" else COLOR_RED

        embed = discord.Embed(description=f"{realm_name} Status", color=color)
        embed.set_author(name="WoW Realm Status", icon_url=AUTHOR_ICON_IMAGE)
        embed.add_field(name="Status", value=realm_status, inline=True)
        embed.add_field(name="Population", value=realm_population, inline=True)
        embed.add_field(name="Queue", value=realm_queue, inline=True)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in realm command: {str(e)}\n{realm_obj}")


@tree.command(name="profile", description="Test")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.channel.id))
async def realm(
    interaction: discord.Interaction,
) -> None:
    await interaction.response.defer()
    profile = blizzard_api.wow.get_account_profile_summary("us", "en_US")
    print(profile)


@tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True,
        )
        logging.info(
            f"Cooldown. {interaction.command.name}, {interaction.user.name} ({interaction.user.id}), {interaction.guild.name}, {interaction.channel.name} ({interaction.channel.id})"
        )


@client.event
async def on_ready():
    await tree.sync()
    logging.info(f"Logged in as {client.user}")


if __name__ == "__main__":
    client.run(config.BOT_SECRET_KEY)
