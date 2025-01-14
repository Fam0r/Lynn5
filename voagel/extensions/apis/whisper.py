import re
import base64
import aiohttp
from io import BytesIO

import discord
from discord.ext import commands
from discord import app_commands
from voagel.main import Bot, EMBED_COLOR

class WhisperCommand(commands.Cog):
    """Whisper"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.tree.add_command(app_commands.ContextMenu(
            name='Transcribe',
            callback=self.auto_transcribe
        ))
        self.bot.tree.add_command(app_commands.ContextMenu(
            name='Transcribe (Translate)',
            callback=self.auto_translate
        ))


    async def do_transcribe(self, audio: bytes, content_type: str, task: str = 'transcribe') -> str:
        data = aiohttp.FormData()
        data.add_field('audio_file',
                       audio,
                       content_type=content_type)
        req = await self.bot.session.post(f'{self.bot.config["apis"]["whisper"]}/asr?encode=true&task={task}&vad_filter=true&output=txt', data=data)

        if req.status != 200:
            raise Exception(f'Failed to transcribe file: {req.status}')

        return await req.text(encoding='utf-8')

    async def auto_translate(self, inter: discord.Interaction, message: discord.Message):
        """
        Transcribe
        """
        if len(message.attachments) > 0:
            link = message.attachments[0].url
        else:
            link = re.search(r'https?://\S+', message.content)
            if not link:
                raise Exception('Could not find audio in the specified message.')
            link = link.group()

        await inter.response.defer()
        req = await self.bot.session.get(link)
        audio = await req.read()
        res = await self.do_transcribe(audio, req.content_type, task='translate')

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_footer(text='Whisper', icon_url=self.bot.get_asset('oai.png'))
        embed.description = f'```\n{res}\n```'
        await inter.followup.send(embed=embed)

    async def auto_transcribe(self, inter: discord.Interaction, message: discord.Message):
        """
        Transcribe
        """
        if len(message.attachments) > 0:
            link = message.attachments[0].url
        else:
            link = re.search(r'https?://\S+', message.content)
            if not link:
                raise Exception('Could not find audio in the specified message.')
            link = link.group()

        await inter.response.defer()
        req = await self.bot.session.get(link)
        audio = await req.read()
        res = await self.do_transcribe(audio, req.content_type)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_footer(text='Whisper', icon_url=self.bot.get_asset('oai.png'))
        embed.description = f'```\n{res}\n```'
        await inter.followup.send(embed=embed)

    @app_commands.command(name='transcribe')
    async def transcribe(self,
        inter: discord.Interaction,
        attachment: discord.Attachment | None = None,
        link: str | None = None
    ):
        """
        Transcribe

        Parameters
        ----------
        link: Link to audio
        attachment: Audio
        """

        if attachment:
            if link:
                raise Exception('Both attachment and link provided. Please only enter one')
            link = attachment.url

        if not link:
            raise Exception('No link or attachment provided')

        await inter.response.defer()
        req = await self.bot.session.get(link)
        audio = await req.read()
        res = await self.do_transcribe(audio, req.content_type)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_footer(text='Whisper', icon_url=self.bot.get_asset('oai.png'))
        embed.description = f'```\n{res}\n```'
        await inter.followup.send(embed=embed)

async def setup(bot: Bot):
    await bot.add_cog(WhisperCommand(bot))
