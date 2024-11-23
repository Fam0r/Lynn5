import discord
from discord.ext import commands
from discord import app_commands

from voagel.main import Bot

class ModCommands(commands.Cog):
    """Moderator Commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name='hackban')
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def hackban(self,
        inter: discord.Interaction,
        id: int,
        reason: str = ''
    ):
        """Ban an user by their ID

        Parameters
        ----------
        id: User ID
        reason: Reason
        """
        assert inter.guild
        snowflake = discord.Object(id)
        await inter.guild.ban(snowflake, reason=reason, delete_message_days=0)
        baninfo = await inter.guild.fetch_ban(snowflake)
        await inter.response.send_message(f'{baninfo.user.name}#{baninfo.user.discriminator} has been banned.')

    @app_commands.command(name='purge')
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self,
        inter: discord.Interaction,
        count: app_commands.Range[int, 0, 100],
        user: discord.Member | None = None
    ):
        """Purge the last {count} messages from the channel.

        Parameters
        ----------
        count: How many messages to purge
        user: Only purge messages from a specific user
        """
        assert isinstance(inter.channel, discord.TextChannel)

        if user:
            deleted = await inter.channel.purge(limit=count, check=lambda m: m.author.id == user.id)
        else:
            deleted = await inter.channel.purge(limit=count)

        await inter.response.send_message(f'Deleted {len(deleted)} messages.', ephemeral=True)

async def setup(bot: Bot):
    await bot.add_cog(ModCommands(bot))
