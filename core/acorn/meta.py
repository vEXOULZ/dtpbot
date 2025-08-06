import uuid
import asyncio
import datetime as dt
from typing import TYPE_CHECKING
import os
from copy import copy

import psutil
from twitchio.ext import commands

from core.utils.ws_send import beauty
from core.acorn.base import Acorn
from core.utils.logger import get_log
from core.utils.timeit import TimeThis
from core.utils.units import strfdelta, strfbytes
from core.nut.nut import CommandNut, DEFAULT_ALIAS, CronNut
from core.nut.restrictions import cooldown, PRIVILEDGE, channel, restrict, get_priviledge, fullname_only
from core.config import BOTNAME
from twitchio import Channel

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

        await ctx.send(beauty(f'latency: {time} | uptime: {uptime} | alloc: {mem_usage}'))

    @CommandNut()
    @cooldown(10, exception = PRIVILEDGE.NOBODY)
    async def ping(self, ctx: commands.Context):
        await self._ping(ctx)

    @CronNut('*/5 * * * *')
    async def ping_cron(self, ctx: commands.Context):
        new_channel = copy(ctx.channel)
        new_channel.name = ctx.bot.nick
        ctx.channel = new_channel
        await self._ping(ctx)

    @CommandNut(default_aliases=DEFAULT_ALIAS.FULLNAME_ONLY)
    @cooldown(10, exception = PRIVILEDGE.NOBODY)
    async def fullping(self, ctx: commands.Context):
        await self._ping(ctx)
        # await self._redis(ctx)

    # @CommandNut
    @channel([BOTNAME])
    async def join(self, ctx: commands.Context, channel: str):

        if get_priviledge(ctx) >= PRIVILEDGE.GOD or ctx.author.name == channel.lower():
            await ctx.send(beauty(f"joining channel #{channel.lower()}"))
            await ctx.bot.join_channels([channel.lower()])

    # @CommandNut
    @restrict(PRIVILEDGE.BROADCASTER)
    async def part(self, ctx: commands.Context, channel: str = None):

        if ctx.channel.name not in [ctx.author.name, BOTNAME]:
            # TODO throw error
            return

        if channel is None:
            channel = ctx.author.name

        if channel == BOTNAME:
            # TODO throw error
            return

        await ctx.send(beauty(f"parting channel #{channel.lower()}"))
        await ctx.bot.part_channels([channel.lower()])

    # @CommandNut
    @restrict(PRIVILEDGE.GOD)
    async def echo(self, ctx: commands.Context):
        logging.info(f"#{ctx.channel.name} echoed @{ctx.author.name}'s '{ctx.message.content}'")
        await ctx.send(beauty(ctx.message.content))