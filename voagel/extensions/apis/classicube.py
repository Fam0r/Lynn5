import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from urllib.parse import quote
from voagel.main import EMBED_COLOR, Bot
from voagel.utils import timedelta_format

class ClassicubeCommand(commands.GroupCog, name='classicube'):
    """Classicube commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    FLAGS = {
        'b': 'Banned from legacy forums',
        'd': 'Developer',
        'm': 'Legacy forum moderator',
        'a': 'Legacy forum admin',
        'e': 'Blog editor',
        'p': 'Patron',
        'u': 'Unverified',
        'r': 'Recovering account'
    }

    @app_commands.command()
    async def player(self,
        inter: discord.Interaction,
        username: str
    ):
        """Looks up information about a player

        Parameters
        ----------
        username: Username of the player
        """
        await inter.response.defer()
        username = quote(username)

        req = await self.bot.session.get(f'https://www.classicube.net/api/player/{username}')
        data = await req.json()
        if not data or data['error'] != '':
            raise Exception(data['error'] if data and data['error'] else 'User not found')

        flags = data['flags']
        embed = discord.Embed(title='ClassiCube User', colour=EMBED_COLOR)
        embed.set_footer(text=f'Classicube • ID: {data["id"]}', icon_url=self.bot.get_asset('cc-cube.png'))
        embed.timestamp = datetime.now()
        delta = datetime.now() - datetime.fromtimestamp(data['registered'])

        embed.set_image(url='https://123dmwm.com/img/3d.php?user='+data['username'])
        embed.set_author(name=data['username'], icon_url=f'https://cdn.classicube.net/face/{data["username"]}.png')
        embed.add_field(name='Account created', value=f'<t:{data["registered"]}:F>\n`{timedelta_format(delta)}` ago')

        if flags:
            embed.add_field(name='Notes', value=', '.join([self.FLAGS[n] for n in flags]))
        if data['forum_title']:
            embed.add_field(name='Legacy forum Title', value=data['forum_title'])

        await inter.response.send_message(embed=embed)

async def setup(bot: Bot):
    await bot.add_cog(ClassicubeCommand(bot))
