import uuid
import asyncio
import datetime as dt
from typing import TYPE_CHECKING
import os
from copy import copy

import psutil
from twitchio.ext import commands

from core.acorn.base import Acorn
from core.utils.logger import get_log
from core.utils.timeit import TimeThis
from core.utils.units import strfdelta, strfbytes
from core.nut.nut import CommandNut, DEFAULT_ALIAS, CronNut
from core.nut.error import MissingDataException
from core.nut.result import ECODE, Result
from core.nut.restrictions import cooldown, PRIVILEDGE, channel, restrict, get_priviledge
from core.config import BOTNAME

if TYPE_CHECKING:
    from core.bot import Bot

logging = get_log(__name__)

class MetaAcorn(Acorn):

    _name = 'meta'
    _tag_workers: dict[str, asyncio.Event] = {}

    def __init__(self, bot: 'Bot'):
        super().__init__()

        bot.add_event(self._pong_handler, "event_pong")

        # throw away first measured period's percentage
        psutil.cpu_percent()

    async def _pong_handler(self, parsed: dict):
        tag = self._tag_workers.pop(parsed['message'], None)
        if tag:
            tag.set()

    async def _twitch_ping(self, ctx: commands.Context) -> str:
        unique_tag = str(uuid.uuid4())

        self._tag_workers[unique_tag] = asyncio.Event()

        with TimeThis() as t:
            await ctx.bot._connection.send(f"PING {unique_tag}")

            try:
                async with asyncio.timeout(5):
                    await self._tag_workers[unique_tag].wait()
            except TimeoutError:
                self._tag_workers.pop(unique_tag, None)
                return "error"

        return strfdelta(t.time)

    async def _ping(self, ctx: commands.Context):
        time   = await self._twitch_ping(ctx)
        uptime = strfdelta(dt.datetime.now() - ctx.bot.start_time)
        pid = os.getpid()
        mem_usage = psutil.Process(pid).memory_info().rss # bytes
        mem_usage = strfbytes(mem_usage)

        return {
            'latency': time,
            'uptime': uptime,
            'alloc': mem_usage,
        }

    @cooldown(10)
    @CommandNut()
    async def ping(self, ctx: commands.Context):
        stats = await self._ping(ctx)
        return Result(ECODE.OK, f"latency: {stats['latency']} ▲ uptime: {stats['uptime']} ▲ alloc: {stats['alloc']}")

    @CronNut('*/15 * * * *')
    async def ping_cron(self, ctx: commands.Context):
        stats = await self._ping(ctx)
        return Result(ECODE.OK, f"heartbeat ❤️ latency: {stats['latency']} ▲ uptime: {stats['uptime']} ▲ alloc: {stats['alloc']}")

    @cooldown(10)
    @CommandNut(default_aliases=DEFAULT_ALIAS.FULLNAME_ONLY)
    async def fullping(self, ctx: commands.Context):
        stats = await self._ping(ctx)
        return Result(ECODE.OK, f"latency: {stats['latency']} ▲ uptime: {stats['uptime']} ▲ alloc: {stats['alloc']}")
        # await self._redis(ctx)FTOD

    @channel([BOTNAME])
    @CommandNut()
    async def join(self, ctx: commands.Context, channel: str):

        if get_priviledge(ctx) >= PRIVILEDGE.ADMIN or ctx.author.name == channel.lower():
            await ctx.bot.join_channels([channel.lower()])
            return Result(ECODE.OK, f"joining channel #{channel.lower()}")

    @restrict(PRIVILEDGE.BROADCASTER)
    @CommandNut()
    async def part(self, ctx: commands.Context, channel: str = None):

        if ctx.channel.name not in [ctx.author.name, BOTNAME]:
            return Result(ECODE.SILENT, None)

        if channel is None:
            channel = ctx.author.name

        channel = channel.lower()

        if channel == BOTNAME:
            raise MissingDataException(f"Cannot part #{channel} due to: my channel")

        await ctx.bot.part_channels([channel])
        return Result(ECODE.OK, f"parting channel #{channel}")

    @restrict(PRIVILEDGE.ADMIN)
    @CommandNut()
    async def echo(self, ctx: commands.Context):
        logging.info(f"#{ctx.channel.name} echoed @{ctx.author.name}'s '{ctx.message.content}'")
        return Result(ECODE.OK, ctx.message.content)