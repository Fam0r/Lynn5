from io import BytesIO
from urllib.parse import quote
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from voagel.main import Bot, EMBED_COLOR


class CVECommand(commands.Cog):
    """CVE"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command()
    async def cve(self,
        inter: discord.Interaction,
        query: str
    ):
        """
        Find information about a CVE

        Parameters
        ----------
        query: CVE identifier
        """

        await inter.response.defer()
        req = await self.bot.session.get(
            f'https://cvedb.shodan.io/cve/{quote(query)}'
        )

        if req.status != 200:
            err = await req.json()
            if not err or 'detail' not in err:
                err = '[unknown error]'
            else:
                err = err['detail']

            raise Exception(f'Got an error status {req.status}', err)

        data = await req.json()

        severity = data['cvss']
        sevstr = 'None' if severity == 0 else 'Low' if severity < 4 else 'Medium' if severity < 7 else 'High' if severity < 9 else 'Critical' if severity < 10 else 'Unknown'

        embed = discord.Embed(color=EMBED_COLOR, title=data['cve_id'], description=data['summary'])
        embed.set_footer(text=f'{severity} {sevstr} (v{data["cvss_version"]})')
        embed.timestamp = datetime.fromisoformat(data['published_time'])

        if data['references']:
            embed.url = data['references'][0]
            assert embed.description
            embed.description += '\n' + ' '.join([f'[[{x+1}]]({y})' for x,y in enumerate(data['references'])])

        await inter.followup.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(CVECommand(bot))
