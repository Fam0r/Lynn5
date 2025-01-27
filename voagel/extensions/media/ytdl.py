import os
import tempfile
import functools
import asyncio
import re

import discord
from discord.ext import commands
from discord import app_commands

from voagel.main import Bot
from voagel.utils import bytes2human, re_encode

try:
    import yt_dlp as yt_dl # type: ignore
except ImportError:
    import youtube_dl as yt_dl # type: ignore

class YtdlCommand(commands.Cog):
    """Youtube-DL command."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name='dl')
    async def ytdl(self,
        inter: discord.Interaction,
        link: str
    ):
        """Download any video on the internet

        Parameters
        ----------
        link: Link to the video
        """
        await inter.response.send_message('Downloading...')

        ydl_opts = {
            'geo_bypass': True,
            'no_color': True,
            'restrictfilenames': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            'format': 'b[filesize<25M]/b[filesize_approx<25M]/bv[filesize<20M]+ba[filesize<5M]/bv[filesize_approx<20M]+ba[filesize_approx<5M]/b[ext=mp4]/bv[ext=mp4]+ba/b/bv+ba'
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # TODO: Download in a separate thread and async
            try:
                ydl_opts['outtmpl'] = tmpdir + '/%(id)s.%(ext)s'
                with yt_dl.YoutubeDL(ydl_opts) as ydl:

                    info = await self.bot.loop.run_in_executor(None, functools.partial(ydl.extract_info, link, download=False))
                    if not info:
                        raise yt_dl.DownloadError(f'Could not get file info')

                    if 'is_live' in info and info['is_live']:
                        raise yt_dl.DownloadError('Cannot download a livestream')
                    if 'filesize' in info and info['filesize']:
                        if info['filesize'] > 26214400:
                            await inter.delete_original_response()
                            raise yt_dl.DownloadError(f'File is too large! ({bytes2human(info["filesize"])})')
                    elif 'filesize_approx' in info and info['filesize_approx']:
                        if info['filesize_approx'] > 28214400:
                            await inter.delete_original_response()
                            raise yt_dl.DownloadError(f'File is too large! ({bytes2human(info["filesize_approx"])})')
                    else:
                        await inter.edit_original_response(content='Could not estimate the size of the file. This download might not finish.')

                future = self.bot.loop.run_in_executor(None, ydl.download, link)
                await asyncio.wait_for(future, 120) # Timeout download after 120 second # WARN: This does not kill the ytdl download, it just gives up waiting for it. The download will stay in the background, draining system resources

                if not isinstance(info, dict):
                    raise yt_dl.DownloadError('Something went wrong with the download.')

                fp = tmpdir + '/' + info['id'] + '.' + info['ext']

                if re.match(r'(^|https?:\/\/)(vm\.|www\.)?tiktok.com', link):
                    await re_encode(fp)

                size = os.path.getsize(fp)
                if size > 8388608: # 8 MiB
                    raise yt_dl.DownloadError(f'File is too large! ({bytes2human(size)})')

                file = discord.File(fp, filename=info['id'] + '.' + info['ext'], description='Source: ' + link)
                await inter.edit_original_response(content='', attachments=[file])
            except FileNotFoundError as e:
                raise yt_dl.DownloadError('Could not download video.') from e

async def setup(bot: Bot):
    await bot.add_cog(YtdlCommand(bot))
