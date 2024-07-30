import os
import sys
import logging
import discord  # type: ignore
from datetime import datetime
from dotenv import load_dotenv  # type: ignore
from discord import app_commands  # type: ignore
from blizzardapi2 import BlizzardApi  # type: ignore

load_dotenv()

blizzard_api = BlizzardApi(os.getenv("BNET_CLIENT_ID"), os.getenv("BNET_CLIENT_SECRET"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
client.tree = tree

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

author_icon_image = "https://i.imgur.com/is26wrA.jpeg"


@tree.command(name="ping", description="Is the bot responding?")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        f"Pong! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ephemeral=True
    )

    logging.info(
        f"{interaction.command.name}, {interaction.user.name} ({interaction.user.id}), {interaction.guild.name}, {interaction.channel.name} ({interaction.channel.id})"
    )


@tree.command(name="tww", description="Countdown to The War Within")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.channel.id))
async def tww(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    try:
        tww_release = datetime(2024, 8, 26, 17, 00, 00) - datetime.now()
        formatted_tww_release = f"{tww_release.days} days, {tww_release.seconds // 3600} hours, {tww_release.seconds // 60 % 60} minutes, {tww_release.seconds % 60} seconds"

        formatted_tww_ea = f"{tww_release.days - 4} days, {tww_release.seconds // 3600} hours, {tww_release.seconds // 60 % 60} minutes, {tww_release.seconds % 60} seconds"

        embed = discord.Embed(description="", color=0x00FF00)
        embed.set_author(
            name="Countdown to The War Within",
            icon_url=author_icon_image,
        )
        embed.set_image(url="https://i.imgur.com/jJnPkKA.png")
        embed.add_field(
            name="Full Release (8/26)", value=formatted_tww_release, inline=True
        )
        embed.add_field(name="Early Access (8/22)", value=formatted_tww_ea, inline=True)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")
        logging.error(f"An error occurred: {str(e)}")

    logging.info(
        f"{interaction.command.name}, {interaction.user.name} ({interaction.user.id}), {interaction.guild.name}, {interaction.channel.name} ({interaction.channel.id})"
    )


@tree.command(name="token", description="Get the current WoW token value")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.channel.id))
async def token(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    try:
        
        token_obj = blizzard_api.wow.game_data.get_token_index("us", "en_US")
        price: int = token_obj["price"]

        formatted_price = f"**{price // 10000:,}** gold"
        
        formatted_time = datetime.fromtimestamp(token_obj["last_updated_timestamp"]).strftime('%Y-%m-%d %H:%M:%S')

        embed = discord.Embed(description=formatted_price, color=0x00FF00)
        embed.set_author(name="Current Token Price", icon_url=author_icon_image)
        embed.set_footer(text=f"As of {formatted_time}")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")
        logging.error(f"An error occurred: {str(e)}\n\nResponse from server:\n\n{token_obj}")

    logging.info(
        f"{interaction.command.name}, {interaction.user.name} ({interaction.user.id}), {interaction.guild.name}, {interaction.channel.name} ({interaction.channel.id})"
    )


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


client.run(os.getenv("BOT_SECRET_KEY"))
