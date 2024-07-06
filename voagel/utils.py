import typing
import asyncio
import os
import html.parser
from datetime import timedelta

async def re_encode(fp: str) -> None:
    if not os.path.exists(fp):
        raise Exception("File passed to Re-Encode doesn't exist")

    out = await check_output(['ffmpeg', '-y', '-i', fp, '-c:a', 'copy', f'{os.path.split(fp)[0]}/2{os.path.split(fp)[1]}'])
    if not os.path.exists(f'{os.path.split(fp)[0]}/2{os.path.split(fp)[1]}'):
        raise Exception('Video encoding failed: \n'+out)
    os.replace(f'{os.path.split(fp)[0]}/2{os.path.split(fp)[1]}', fp)

def bytes2human(n: int) -> str:
    symbols = ('KiB', 'MiB', 'GiB', 'TiB', 'PiB')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return f'{value:.1f}{s}'
    return f'{n}B'

async def subprocess(*args, **kwargs):
    proc = await asyncio.create_subprocess_exec(*args, **kwargs)
    try:
        await proc.wait()
        return proc
    except asyncio.CancelledError:
        proc.terminate()
        raise

async def check_output(args: typing.List[str], timeout: int = 120, raise_on_error: bool = False):
    proc = await asyncio.wait_for(subprocess(args[0], *args[1:], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT), timeout)
    assert proc.stdout
    out = await proc.stdout.read()
    out = out.decode('utf-8')

    if raise_on_error and proc.returncode != 0:
        raise Exception(f'Shell process for `{args[0]}` exited with status `{proc.returncode}`')
    return out

class OpenGraphParser(html.parser.HTMLParser):
    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.tags = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        k = v = None
        for attr in attrs:
            if attr[0].lower() == 'name' or attr[0].lower() == 'property' and attr[1] and attr[1].startswith('og:'):
                k = attr[1]
            if attr[0].lower() == 'content':
                v = attr[1]
        if k and v:
            self.tags[k] = v

def timedelta_format(delta: timedelta):
    ret = []
    num_years = int(delta.days / 365)
    if num_years > 0:
        delta -= timedelta(days=num_years * 365)
        ret.append(f'{num_years} years')

    if delta.days > 0:
        ret.append(f'{delta.days} days')

    num_hours = int(delta.seconds / 3600)
    if num_hours > 0:
        delta -= timedelta(hours=num_hours)
        ret.append(f'{num_hours} hours')

    num_minutes = int(delta.seconds / 60)
    if num_minutes > 0:
        ret.append(f'{num_minutes} minutes')

    if not ret:
        ret.append('Less than a minute')
    return ' '.join(ret)
