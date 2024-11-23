import discord
from discord.ext import commands
from discord import app_commands
from typing import Any
import json
import base64
from datetime import datetime
import socket
import time
import struct
from io import BytesIO
from voagel.main import Bot, EMBED_COLOR


class MinecraftCommands(commands.GroupCog, name='minecraft'):
    """Minecraft Commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    LEGACY_COLOR_MAP = {
        '0': '\033[30m',
        '1': '\033[34m',
        '2': '\033[32m',
        '3': '\033[36m',
        '4': '\033[31m',
        '5': '\033[35m',
        '6': '\033[33m',
        '7': '\033[0m',
        '8': '\033[0m',
        '9': '\033[34m',
        'a': '\033[32m',
        'b': '\033[36m',
        'c': '\033[31m',
        'd': '\033[35m',
        'e': '\033[33m',
        'f': '\033[37m',
        'k': '\033[9m',
        'l': '\033[1m',
        'm': '\033[9m',
        'n': '\033[4m',
        'o': '\033[3m',
        'r': '\033[0m',
    }

    COLOR_MAP = {
        'black': '\033[30m',
        'dark_blue': '\033[34m',
        'dark_green': '\033[32m',
        'dark_aqua': '\033[36m',
        'dark_red': '\033[31m',
        'dark_purple': '\033[35m',
        'gold': '\033[33m',
        'gray': '\033[0m',
        'dark_gray': '\033[0m',
        'blue': '\033[34m',
        'green': '\033[32m',
        'aqua': '\033[36m',
        'red': '\033[31m',
        'light_purple': '\033[35m',
        'yellow': '\033[33m',
        'white': '\033[37m',
        'obfuscated': '\033[9m',
        'bold': '\033[1m',
        'strikethrough': '\033[9m',
        'underline': '\033[4m',
        'italic': '\033[3m',
        'reset': '\033[0m',
    }

    async def get_UUID(self, name: str) -> tuple[str, str]:
        req = await self.bot.session.get(f'https://api.mojang.com/users/profiles/minecraft/{name}')
        if req.status == 200:
            j = json.loads(await req.text())
            if 'id' in j:
                return (j["name"], j['id'])

        req = await self.bot.session.get(f'https://api.mojang.com/users/profiles/minecraft/{name}?at=0')
        if req.status == 200:
            j = json.loads(await req.text())
            if 'id' in j:
                return (j["name"], j['id'])

        raise Exception('Player not found')

    async def get_skin(self, uuid: str) -> dict:
        req = await self.bot.session.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}')
        j = await req.json()
        try:
            val = j['properties'][0]['value']
        except KeyError as e:
            raise Exception("Mojang's servers didn't return valid skin data.") from e

        return json.loads(base64.b64decode(val))

    def _unpack_varint(self, sock):
        data = 0
        for i in range(5):
            ordinal = sock.recv(1)

            if len(ordinal) == 0:
                break

            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7*i

            if not byte & 0x80:
                break

        return data

    def _pack_varint(self, data):
        ordinal = b''

        while True:
            byte = data & 0x7F
            data >>= 7
            ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

            if data == 0:
                break

        return ordinal

    def _pack_data(self, data):
        """ Page the data """
        if isinstance(data, str):
            data = data.encode('utf8')
            return self._pack_varint(len(data)) + data
        elif isinstance(data, int):
            return struct.pack('H', data)
        elif isinstance(data, float):
            return struct.pack('L', int(data))
        else:
            return data

    def _send_data(self, connection, *args):
        """ Send the data on the connection """
        data = b''

        for arg in args:
            data += self._pack_data(arg)

        connection.send(self._pack_varint(len(data)) + data)

    def _read_fully(self, connection, extra_varint=False):
        """ Read the connection and return the bytes """
        packet_length = self._unpack_varint(connection)
        packet_id = self._unpack_varint(connection)
        byte = b''

        if extra_varint:
            # Packet contained netty header offset for this
            if packet_id > packet_length:
                self._unpack_varint(connection)

            extra_length = self._unpack_varint(connection)

            while len(byte) < extra_length:
                byte += connection.recv(extra_length)

        else:
            byte = connection.recv(packet_length)

        return byte


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

        user, uuid = await self.get_UUID(username)
        skin = await self.get_skin(uuid)

        embeds = []
        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name=user, icon_url=f'https://crafatar.com/avatars/{uuid}.png')
        embed.set_footer(text=f'Minecraft', icon_url=self.bot.get_asset('minecraft.png'))
        embed.timestamp = datetime.now()
        embed.set_image(url=f'https://crafatar.com/renders/body/{uuid}.png')

        embed.add_field(name='UUID', value=uuid)
        try:
            embed.add_field(name='Skin URL', value='[Click me]('+skin['textures']['SKIN']['url']+')')
        except KeyError:
            pass
        embeds.append(embed)

        if 'CAPE' in skin['textures']:
            embed = discord.Embed(title='Minecraft Cape', color=EMBED_COLOR)
            embed.set_author(name=user, icon_url=f'https://crafatar.com/avatars/{uuid}.png')
            embed.set_image(url=skin['textures']['CAPE']['url'])
            embeds.append(embed)

        of = await self.bot.session.get(f'http://s.optifine.net/capes/{user}.png')
        if of.status == 200:
            embed = discord.Embed(title='Optifine Cape', color=EMBED_COLOR)
            embed.set_author(name=user, icon_url=f'https://crafatar.com/avatars/{uuid}.png')
            embed.set_image(url=f'http://s.optifine.net/capes/{user}.png')
            embeds.append(embed)

        await inter.followup.send(embeds=embeds)

    def query_server(self, ip: str, port: str) -> dict[str, Any]:
        valid = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
                conn.settimeout(5)
                conn.connect((ip, port))
                valid = True

                # Send handshake + status request
                self._send_data(conn, b'\x00\x00', ip, port, b'\x01')
                self._send_data(conn, b'\x00')

                # Read response, offset for string length
                data = self._read_fully(conn, extra_varint=True)

                # Send and read unix time
                unix = time.time()
                self._send_data(conn, b'\x01', 123)
                _ = self._read_fully(conn)
                ping = int((time.time() - unix) * 1000)

                data = json.loads(data.decode('utf8'))
                data['ping'] = ping

                return data
        except socket.timeout as e:
            if not valid:
                raise Exception('Could not connect to server. Make sure the IP is valid.') from e
            raise e

    @app_commands.command()
    async def server(self,
        inter: discord.Interaction,
        address: str
    ):
        """Looks up information about a server

        Parameters
        ----------
        address: Host/IP (and optionally port) of the Minecraft server
        """
        await inter.response.defer()

        port = int(25565 if not ':' in address else address.split(':')[-1])
        ip = address.split(':')[0]

        data = await self.bot.loop.run_in_executor(None, self.query_server, ip, port)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.timestamp = datetime.utcnow()
        embed.title = ip + (f':{port}' if port != 25565 else '')
        embed.set_footer(text='Minecraft', icon_url=self.bot.get_asset('minecraft.png'))

        favicon = None
        if 'favicon' in data and data['favicon']:
            favicon = discord.File(BytesIO(base64.b64decode(data['favicon'].replace('data:image/png;base64,', ''))), 'pack.png')
            embed.set_thumbnail(url='attachment://pack.png')
        else:
            embed.set_thumbnail(url=self.bot.get_asset('mc_server.png'))

        if isinstance(data['description'], dict):
            # json text format
            desc = data['description']
            description = ''
            for obj in desc:
                if obj == 'extra':
                    for extra in desc[obj]:
                        if 'color' in extra:
                            description += self.COLOR_MAP.get(extra['color'], '')
                        if 'bold' in extra:
                            description += self.COLOR_MAP['bold']
                        if 'italic' in extra:
                            description += self.COLOR_MAP['italic']
                        if 'strikethrough' in extra:
                            description += self.COLOR_MAP['strikethrough']
                        if 'underline' in extra:
                            description += self.COLOR_MAP['underline']
                        if 'text' in extra:
                            description += extra['text']

                        description += self.COLOR_MAP['reset']
                elif obj == 'text':
                    description += desc[obj]

            lines = []
            for line in description.split('\n'):
                lines.append(line.strip())
            description = '\n'.join(lines)
        else:
            description = ''
            lines = []
            # Strip whitespace
            for line in data['description'].split('\n'):
                lines.append(line.strip())
            data['description'] = '\n'.join(lines)

            for i in range(len(data['description'])):
                # (Try to) clean up colorcodes from description
                if i > 0 and data['description'][i-1] == '§' and data['description'][i] in self.LEGACY_COLOR_MAP:
                    description = description[:-1] # Remove last §
                    description += self.LEGACY_COLOR_MAP[data['description'][i]]
                else:
                    description += data['description'][i]
        embed.description = f'```ansi\n{description}\n```'

        embed.add_field(name='Version', value=data['version']['name'])
        embed.add_field(name='Players', value=f"{data['players']['online']}/{data['players']['max']}")
        embed.add_field(name='Ping', value=f"{data['ping']}ms")

        if 'modinfo' in data:
            if data['modinfo']['type'] == 'FML':
                embed.add_field(name='Forge Server', value=f"{len(data['modinfo']['modList'])} mods enabled.")
            else:
                embed.add_field(name='Modded Server', value=f"Type: {data['modinfo']['type']}")
        elif 'forgeData' in data:
            embed.add_field(name='Forge Server', value=f"{len(data['forgeData']['mods'])} mods enabled.")

        if favicon:
            await inter.followup.send(embed=embed, file=favicon)
        else:
            await inter.followup.send(embed=embed)

async def setup(bot: Bot):
    await bot.add_cog(MinecraftCommands(bot))
