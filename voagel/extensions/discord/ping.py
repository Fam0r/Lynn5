import discord
from discord.ext import commands
from discord import app_commands

from voagel.main import Bot

class PingCommand(commands.Cog):
    """Ping command"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command()
    async def ping(self, inter: discord.Interaction):
        """Get the bot's current websocket latency."""
        await inter.response.send_message(f"pong: {round(self.bot.latency * 1000)}ms")

async def setup(bot: Bot):
    await bot.add_cog(PingCommand(bot))
