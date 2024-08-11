import disnake
from disnake.ext import commands

from voagel.main import Bot, EMBED_COLOR

class TranslateCommand(commands.Cog):
    """Translate"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.gcp_languages = []

    async def get_languages(self) -> Dict[str, str]:
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
                self.gcp_languages[l['language']] = l['name']

        return self.gcp_languages

    async def language_autocomplete(self, string: str) -> List[str]:
        """Autocomplete languages"""

        out = []

        for _, lang in await self.get_languages():
            try:
                if string.lower() in lang.lower():
                    out.append(lang)
            except Exception:
                pass

        return out[:25]


    async def do_translate(self, fromlang: str | None, tolang: str, query: str):
        params = {
            'q': [query],
            'target': tolang,
            'key': self.bot.get_api_key('gcp_translate')
        }
        if fromlang:
            params['source'] = fromlang

        req = await self.bot.session.post(f'https://translation.googleapis.com/language/translate/v2', params=params)
        data = await req.json()

        if 'error' in data:
            raise Exception('Google Translate returned an error: ' + str(data['error']))

        return data['data']

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
        data = (await self.do_translate(None, 'en', query))['translations'][0]

        inlang = (await self.get_languages()).get(data['detectedSourceLanguage'], data['detectedSourceLanguage'])

        embed = disnake.Embed(color=EMBED_COLOR)
        embed.add_field(f'From `{inlang}`', f'```\n{query}\n```', inline=False)
        embed.add_field('To `English`', f'```\n{data["translatedText"]}\n```', inline=False)
        embed.set_footer(text='Google Translate', icon_url=self.bot.get_asset('google_translate.png'))
        await inter.send(embed=embed)

    @commands.slash_command()
    async def translate(self,
        inter: disnake.ApplicationCommandInteraction,
        query: str,
        _from: str = commands.Param('auto', name='from', autocomplete=language_autocomplete),
        to: str = commands.Param('eng', autocomplete=language_autocomplete)
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
        inlang = None
        outlang = None

        if fromlang:
            inlang = (await self.get_languages()).get(fromlang)
            if not inlang:
                raise commands.BadArgument(f'No language found by `{_from}`')

        outlang = (await self.get_languages()).get(tolang)
        if not outlang:
            raise commands.BadArgument(f'No language found by `{to}`')

        data = (await self.do_translate(fromlang, tolang, query))['translations'][0]

        if not inlang:
            inlang = (await self.get_languages()).get(data['detectedSourceLanguage'], data['detectedSourceLanguage'])

        embed = disnake.Embed(color=EMBED_COLOR)
        embed.add_field(f'From `{inlang}`', f'```\n{query}\n```', inline=False)
        embed.add_field(f'To `{outlang}`', f'```\n{data["translatedText"]}\n```', inline=False)
        embed.set_footer(text='Google Translate', icon_url=self.bot.get_asset('google_translate.png'))
        await inter.send(embed=embed)

def setup(bot: Bot):
    bot.add_cog(TranslateCommand(bot))
