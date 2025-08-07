import uuid
import asyncio
import datetime as dt
from typing import TYPE_CHECKING
import os
from collections import deque

import psutil
from twitchio.ext import commands

from core.acorn.base import Acorn
from core.utils.logger import get_log
from core.utils.timeit import TimeThis
from core.utils.units import strfdelta, strfbytes
from core.utils.graph import generate_graph_string
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

    # 2h
    latency_hist   = deque([dt.timedelta()] * 120, 120)
    cpu_usage_hist = deque([0]              * 120, 120)
    mem_usage_hist = deque([0]              * 120, 120)
    beat           = False

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

        return t.time

    async def _ping(self, ctx: commands.Context):
        time   = await self._twitch_ping(ctx)
        pid = os.getpid()
        mem_usage = psutil.Process(pid).memory_info().rss # bytes
        cpu_perc = psutil.cpu_percent()

        return {
            'latency': time,
            'alloc': mem_usage,
            'cpu': cpu_perc,
        }

    @cooldown(10)
    @CommandNut()
    async def ping(self, ctx: commands.Context):
        stats = await self._ping(ctx)

        uptime  = strfdelta(dt.datetime.now() - ctx.bot.start_time)
        latency = strfdelta(stats['latency'])
        alloc   = strfbytes(stats['alloc'])
        cpu     = str(stats['cpu'])

        return Result(ECODE.OK, f"pong ▲ latency: {latency} ▲ uptime: {uptime} ▲ alloc: {alloc} ▲ cpu: {cpu}")

    @CronNut('*/1 * * * *')
    async def heartbeat(self, ctx: commands.Context):
        stats = await self._ping(ctx)

        self.latency_hist.append(stats['latency'])
        self.mem_usage_hist.append(stats['alloc'])
        self.cpu_usage_hist.append(stats['cpu'])

        self.beat = True

        return Result(ECODE.SILENT, None)

    @cooldown(10)
    @CommandNut(default_aliases=DEFAULT_ALIAS.FULLNAME_ONLY)
    async def fullping(self, ctx: commands.Context):
        if not self.beat:
            await self.heartbeat.actuate()

        uptime  = strfdelta(dt.datetime.now() - ctx.bot.start_time)
        latency = strfdelta(self.latency_hist[-1])
        alloc   = strfbytes(self.mem_usage_hist[-1])
        cpu     = str(self.cpu_usage_hist[-1])

        return Result(ECODE.OK, [
            f"fullpong ▲ uptime: {uptime}",
            f"fullpong ▲ latency ▲ 2h hist: {generate_graph_string([x.total_seconds() for x in self.latency_hist], cbfmt=strfdelta)} latest: {latency}",
            f"fullpong ▲ alloc ▲ 2h hist: {generate_graph_string(self.mem_usage_hist, cbfmt=strfbytes)} latest: {alloc}",
            f"fullpong ▲ cpu ▲ 2h hist: {generate_graph_string(self.cpu_usage_hist, cbfmt=str)} latest: {cpu}",
        ])

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