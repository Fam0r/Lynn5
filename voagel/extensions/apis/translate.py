import disnake
from disnake.ext import commands

from voagel.main import Bot, EMBED_COLOR

class TranslateCommand(commands.Cog):
    """Translate"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.gcp_languages: dict[str, str] = {}

    async def get_languages(self) -> dict[str, str]:
        if not self.gcp_languages:
            params = {
                'target': 'en',
                'key': self.bot.get_api_key('gcp_translate')
            }
            req = await self.bot.session.get(f'https://translation.googleapis.com/language/translate/v2/languages', params=params)
            data = await req.json()

            if 'error' in data:
                raise Exception('Google Translate returned an error: ' + str(data['error']))

            for l in data['data']['languages']:
                self.gcp_languages[l['name']] = l['language']

        return self.gcp_languages

    async def do_translate(self, fromlang: str | None, tolang: str, query: str):
        params = {
            'q': [query],
            'tl': tolang,
            'sl': fromlang if fromlang else 'auto',
            'dt': 't',
            'client': 'gtx',
            'dj': 1,
            'source': 'input'
        }

        req = await self.bot.session.post(f'https://translate.googleapis.com/translate_a/single', params=params)
        data = await req.json()

        if 'error' in data:
            raise Exception('Google Translate returned an error: ' + str(data['error']))

        return data

    async def do_ocr_translate(self, fromlang: str | None, tolang: str, img: bytes):
        ocr_cog = self.bot.get_cog('OcrCommand')
        if not ocr_cog:
            raise commands.errors.DisabledCommand()

        ocr_res: dict = ocr_cog.do_ocr(img) # type: ignore
        print(ocr_res)

    @commands.message_command(name='Auto Translate')
    async def auto_translate(self, inter: disnake.MessageCommandInteraction):
        await inter.response.defer()

        query = inter.target.content
        if not query:
            raise Exception('No text found in message.')
        data = await self.do_translate(None, 'en', query)

        inlang = (await self.get_languages()).get(data['src'], data['src'])

        embed = disnake.Embed(color=EMBED_COLOR)
        embed.add_field(f'From `{inlang}`', f'```\n{query}\n```', inline=False)
        embed.add_field('To `English`', f'```\n{data["sentences"][0]["trans"]}\n```', inline=False)
        embed.set_footer(text='Google Translate', icon_url=self.bot.get_asset('google_translate.png'))

        if 'confidence' in data and data['confidence'] < 1.0:
            embed.description = f'(confidence: {round(data["confidence"]*100, 2)}%)'

        await inter.send(embed=embed)

    @commands.slash_command()
    async def translate(self,
        inter: disnake.ApplicationCommandInteraction,
        query: str,
        _from: str = commands.Param('auto', name='from'),
        to: str = commands.Param('English')
    ):
        """
        Translate stuff using Google Translate. Defaults to Auto-Detect -> English

        Parameters
        ----------
        query: Text to translate
        _from: Language to translate from
        to: Language to translate to
        """

        await inter.response.defer()

        fromlang = _from if _from != 'auto' else None
        tolang = to
        fromcode = None
        tocode = None

        if fromlang:
            fromcode = (await self.get_languages()).get(fromlang)
            if not fromcode:
                raise commands.BadArgument(f'No language found by `{fromlang}`')

        tocode = (await self.get_languages()).get(tolang)
        if not tocode:
            raise commands.BadArgument(f'No language found by `{to}`')

        data = await self.do_translate(fromcode, tocode, query)

        if not fromcode and 'src' in data:
            fromcode = fromlang = data['src']
            for lang, code in (await self.get_languages()).items():
                if fromcode == code:
                    fromlang = lang

        embed = disnake.Embed(color=EMBED_COLOR)
        embed.add_field(f'From `{fromlang}`', f'```\n{query}\n```', inline=False)
        embed.add_field(f'To `{tolang}`', f'```\n{data["sentences"][0]["trans"]}\n```', inline=False)
        embed.set_footer(text='Google Translate', icon_url=self.bot.get_asset('google_translate.png'))

        if 'confidence' in data and data['confidence'] < 1.0:
            embed.description = f'(confidence: {round(data["confidence"]*100, 2)}%)'

        await inter.send(embed=embed)

    @translate.autocomplete('from')
    @translate.autocomplete('to')
    async def language_autocomplete(self, _: disnake.ApplicationCommandInteraction, string: str) -> list[str]:
        """Autocomplete languages"""

        out = []

        for lang, _ in (await self.get_languages()).items():
            try:
                if string.lower() in lang.lower():
                    out.append(lang)
            except Exception:
                pass

        return out[:25]


def setup(bot: Bot):
    bot.add_cog(TranslateCommand(bot))
