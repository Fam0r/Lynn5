import logging
import discord
import sys
import tomllib
import aiohttp
from pathlib import Path
from discord.ext import commands

ERROR_COLOR = 0xff4444
EMBED_COLOR = 0x8f8f8f

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.config = {}
        self.data = {}

        super().__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        self.session = aiohttp.ClientSession(headers={'User-Agent': 'Voagel (Discord Bot) https://github.com/Vocaned/Voagel'})
        logging.info("Bot is ready.")

    async def setup_hook(self) -> None:
        # TODO: clean up this mess
        for extension in [str(f.resolve()).replace('.py', '').replace('/', '.').replace('\\', '.').split('voagel.extensions.')[-1] for f in Path(__file__).parent.rglob('extensions/**/*.py')]:
            try:
                await self.load_extension('voagel.extensions.' + extension)
            except (discord.ClientException, ModuleNotFoundError):
                logging.error('Failed to load extension %s', extension, exc_info=True)

    def get_api_key(self, key: str) -> str:
        val = self.config['secrets'].get(key, None)
        if not val:
            raise commands.DisabledCommand('API key for command missing. Ping the bot owner for help.')
        return val

    def get_asset(self, path: str) -> str:
        return self.config['misc']['asset_url'] + path

    def load_config(self) -> None:
        Path('config').mkdir(exist_ok=True)
        if not Path('config', 'bot.toml').exists():
            logging.critical('Bot config could not be found. Copy bot.toml to the config folder and edit it to continue.')
            sys.exit(1)
        with open(Path('config', 'bot.toml'), 'rb') as f:
            self.config = tomllib.load(f)

def main() -> None:
    bot = Bot(intents=discord.Intents.all(), command_prefix='whythefuckdoihavetoprovideacommandprefixidonthaveanytextcommands...')
    bot.load_config()

    bot.status = discord.Status(bot.config['bot']['status'])

    activities = {'unknown': -1, 'playing': 0, 'streaming': 1, 'listening': 2, 'watching': 3, 'custom': 4, 'competing': 5}
    activitytype = activities.get(bot.config['bot']['activity_type'].lower(), 0)
    bot.activity = discord.Activity(name=bot.config['bot']['activity'], type=activitytype)

    bot.run(bot.get_api_key('discord'))

if __name__ == '__main__':
    main()
