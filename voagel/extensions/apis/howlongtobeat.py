import discord
from discord.ext import commands
from discord import app_commands
from howlongtobeatpy import HowLongToBeat
from voagel.main import Bot, EMBED_COLOR

class HowlongtobeatCommand(commands.Cog):
    """Howlongtobeat command"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command()
    async def howlongtobeat(self,
        inter: discord.Interaction,
        game: str
    ):
        """How long does a game take to beat?

        Parameters
        ----------
        game: Game's name
        """
        results = await HowLongToBeat().async_search(game)
        if results is not None and len(results) > 0:
            result = max(results, key=lambda element: element.similarity)
            embed = discord.Embed(title=result.game_name, url=result.game_web_link, color=EMBED_COLOR)
            embed.add_field(name='Main Story', value=f'{result.main_story} Hours')
            embed.add_field(name='Main + Extra', value=f'{result.main_extra} Hours')
            embed.add_field(name='Completionist', value=f'{result.completionist} Hours')
            embed.set_footer(text='HowLongToBeat', icon_url=self.bot.get_asset('hltb_brand.png'))

            if result.game_image_url:
                embed.set_thumbnail(url=result.game_image_url)

            await inter.response.send_message(embed=embed)
        else:
            raise Exception('Game not found.')

async def setup(bot: Bot):
    await bot.add_cog(HowlongtobeatCommand(bot))
