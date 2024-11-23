import logging
import traceback

import discord
from discord.ext import commands
from discord import app_commands

from voagel.main import Bot, ERROR_COLOR


class Errors(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.tree_on_error

    async def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

    async def tree_on_error(self,
        inter: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return

        assert inter.command
        logging.warning('Ignoring exception in /%s', inter.command.name)
        self.bot.data['last_error'] = '\n'.join(traceback.format_exception(type(error), error, error.__traceback__))

        errtype = '[Unknown Error]'
        errmsg = '[Unknown Error]'

        if isinstance(error, app_commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            if len(missing) > 2:
                fmt = f'{"**, **".join(missing[:-1])}, and {missing[-1]}'
            else:
                fmt = ' and '.join(missing)
            _message = f'The bot is missing the **{fmt}** permission(s) to run this command.'
            errtype = 'Not enough permissions.'
            errmsg = _message
        elif isinstance(error, commands.NSFWChannelRequired):
            errtype = 'This command can only be used in NSFW channels.'
        elif isinstance(error, commands.DisabledCommand):
            errtype = 'This command has been disabled in this server.'
        elif isinstance(error, app_commands.CommandOnCooldown):
            errtype = 'This command is on cooldown'
            errmsg = f'Please try again in {round(error.retry_after)}s'
        elif isinstance(error, app_commands.MissingPermissions):
            missing = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            if len(missing) > 2:
                fmt = f'{"**, **".join(missing[:-1])}, and {missing[-1]}'
            else:
                fmt = ' and '.join(missing)
            errtype = 'Not enough permissions.'
            errmsg = f'You need the **{fmt}** permission(s) to use this command.'
        elif isinstance(error, commands.UserInputError):
            errtype = 'Invalid input.'
        elif isinstance(error, app_commands.NoPrivateMessage):
            errtype = 'This command cannot be used in direct messages.'
        elif isinstance(error, app_commands.CheckFailure):
            errtype = 'You do not have permission to use this command.'
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            errtype = 'Extension already loaded.'
        elif isinstance(error, commands.ExtensionNotFound):
            errtype = 'Extension not found.'
        elif isinstance(error, commands.ExtensionNotLoaded):
            errtype = 'Extension not loaded.'
        elif isinstance(error, commands.ExtensionFailed):
            errtype = 'Failed to load extension.'
        elif isinstance(error, app_commands.CommandInvokeError):
            errtype = f'Uncaught exception occured in `{inter.command.name}`'

            original = getattr(error, 'original', error)
            errmsg = f'{type(original).__name__}: {original}'

        embed = discord.Embed(color=ERROR_COLOR, title=errtype, description=errmsg)
        await inter.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: Bot):
    await bot.add_cog(Errors(bot))
