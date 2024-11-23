import re
import base64
from io import BytesIO

import discord
from discord.ext import commands
from discord import app_commands
from voagel.main import Bot, EMBED_COLOR

SUPPORTED_MIMES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

class OCRCommand(commands.Cog):
    """OCR"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.tree.add_command(app_commands.ContextMenu(
            name='Auto OCR',
            callback=self.auto_ocr
        ))

    async def do_ocr(self, img: bytes) -> dict:
        data={'requests': [{
            'features': [{'type': 'TEXT_DETECTION'}],
            'image': {'content': base64.b64encode(img).decode()}
        }]}
        req = await self.bot.session.post(f'https://content-vision.googleapis.com/v1/images:annotate?key={self.bot.get_api_key("gcp_ocr")}', json=data)
        j = await req.json()

        if 'error' in j:
            raise Exception('Google Vision returned an error: ' + str(j['error']))

        return j['responses'][0]

    async def auto_ocr(self, inter: discord.Interaction, message: discord.Message):
        """
        OCR.
        """
        if len(message.attachments) > 0:
            link = message.attachments[0].url
        else:
            link = re.search(r'https?://\S+', message.content)
            if not link:
                raise Exception('Could not find an image in the specified message.')
            link = link.group()

        await inter.response.defer()
        imgres = await self.bot.session.get(link)

        if imgres.content_type.lower() not in SUPPORTED_MIMES:
            raise Exception(f'Unsupported file type `{imgres.content_type}`.')

        img = await imgres.read()
        res = await self.do_ocr(img)
        if not res['fullTextAnnotation']:
            raise Exception('Did not detect text.')
        else:
            embed = discord.Embed(color=EMBED_COLOR)
            embed.set_footer(text='Google Cloud Vision', icon_url=self.bot.get_asset('gcp.png'))
            embed.description = f'```\n{res["fullTextAnnotation"]["text"]}\n```'
            filename = link.split('/')[-1].split('?')[0]
            file = discord.File(fp=BytesIO(img), filename=filename)
            embed.set_thumbnail(url=f'attachment://{filename}')
            await inter.followup.send(embed=embed, file=file)

    @app_commands.command(name='ocr')
    async def ocr(self,
        inter: discord.Interaction,
        attachment: discord.Attachment | None = None,
        link: str | None = None
    ):
        """
        OCR.

        Parameters
        ----------
        link: Link to image
        attachment: Image
        """

        if attachment:
            if link:
                raise Exception('Both attachment and link provided. Please only enter one')
            link = attachment.url

        if not link:
            raise Exception('No link or attachment provided')

        await inter.response.defer()
        imgres = await self.bot.session.get(link)

        if imgres.content_type.lower() not in SUPPORTED_MIMES:
            raise Exception(f'Unsupported file type `{imgres.content_type}`.')

        img = await imgres.read()
        res = await self.do_ocr(img)
        if not res['fullTextAnnotation']:
            raise Exception('Did not detect text.')
        else:
            embed = discord.Embed(color=EMBED_COLOR)
            embed.set_footer(text='Google Cloud Vision', icon_url=self.bot.get_asset('gcp.png'))
            embed.description = f'```\n{res["fullTextAnnotation"]["text"]}\n```'
            filename = link.split('/')[-1].split('?')[0]
            file = discord.File(fp=BytesIO(img), filename=filename)
            embed.set_thumbnail(url=f'attachment://{filename}')
            await inter.followup.send(embed=embed, file=file)

async def setup(bot: Bot):
    await bot.add_cog(OCRCommand(bot))
