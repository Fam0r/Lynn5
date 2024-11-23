import discord
from discord.ext import commands
from discord import app_commands
import random

from voagel.main import Bot

class RandomCommands(commands.Cog):
    """Random commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command()
    async def dice(self, inter: discord.Interaction, query: str):
        """Rolls n dice with set amount of faces. Default 1d6.

        Parameters
        ----------
        query: Parameters of the dice you want to roll
        """

        if not 'd' in query:
            n = int(query)
            f = 6
        else:
            n = int(query.split('d')[0])
            f = int(query.split('d')[1])

        if n == 0:
            await inter.response.send_message('You roll 0 dice. Nothing happens.')
            return
        if f == 0:
            await inter.response.send_message(f"You roll {n} {'dice' if n > 1 else 'die'} with 0 faces. The world implodes as your zero-dimensional {'dice' if n > 1 else 'die'} hit the table.")
            return

        if f < 0:
            await inter.response.send_message(f"You try to roll {n} {'dice' if n > 1 else 'die'} with negative faces, but you realize that you're all out of negative-dimensional dice.")
            return
        if n < 0:
            roll = random.randint(abs(n), abs(n)*f)
            await inter.response.send_message(f"You roll negative {n} dice. The dice jump from the table back into your hand. You rolled **{roll}**!")
            return

        roll = random.randint(n, n*f)
        await inter.response.send_message(f"You roll {n} {'dice' if n > 1 else 'die'} with {f} face{'s' if f > 1 else ''}. You rolled **{roll}**!")

    @app_commands.command()
    async def coinflip(self, inter: discord.Interaction):
        """Flips a coin"""
        flip = random.randint(0, 6000)
        if flip == 0:
            await inter.response.send_message('You flip a coin. It lands on its edge!')
        else:
            await inter.response.send_message(f"You flip a coin. It lands on **{'heads' if flip < 3000 else 'tails'}**.")

    @app_commands.command()
    async def choose(self, inter: discord.Interaction, choices: str):
        """Choose between a list of things

        Parameters
        ----------
        choices: List of possible choices, separated by a semicolon
        """
        await inter.response.send_message(f"Picked **{random.choice(choices.split(';')).strip()}**.")

async def setup(bot: Bot):
    await bot.add_cog(RandomCommands(bot))
