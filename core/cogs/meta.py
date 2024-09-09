import uuid
import asyncio
import datetime as dt
from typing import TYPE_CHECKING
import os

import psutil
from twitchio.ext import commands

from core.cogs.base import BaseCog
from core.redis.base import redis
from core.utils.timeit import TimeThis
from core.utils.units import strfdelta, strfbytes
from core.decorators.channelwise import channelwise, bot_channel_only

if TYPE_CHECKING:
    from core.bot import Bot

class MetaCog(BaseCog):

    _tag_workers: dict[str, asyncio.Event] = {}

    def __init__(self, bot: 'Bot'):
        super().__init__(bot)

        self._bot._connection._actions['PONG'] = self._pong_handler

        # throw away first measured period's percentage
        psutil.cpu_percent()

    async def _pong_handler(self, parsed: dict):
        tag = self._tag_workers.pop(parsed['message'], None)
        if tag:
            tag.set()

    async def _twitch_ping(self) -> str:
        unique_tag = str(uuid.uuid4())

        self._tag_workers[unique_tag] = asyncio.Event()

        with TimeThis() as t:
            await self._bot._connection.send(f"PING {unique_tag}")

            try:
                async with asyncio.timeout(5):
                    await self._tag_workers[unique_tag].wait()
            except TimeoutError:
                self._tag_workers.pop(unique_tag, None)
                return "error"

        return strfdelta(t.time / 2)

    async def _ping(self, ctx: commands.Context):
        time   = await self._twitch_ping()
        uptime = strfdelta(dt.datetime.now() - self._bot.start_time)
        pid = os.getpid()
        mem_usage = psutil.Process(pid).memory_info().rss # bytes
        mem_usage = strfbytes(mem_usage)

        await ctx.send(f'latency: {time} | uptime: {uptime} | alloc: {mem_usage}')

    async def _redis(self, ctx: commands.Context):
        with TimeThis() as t:
            rstats = redis.memory_stats()
        redis_time = strfdelta(t.time / 2, last_decimals = 3)

        redis_keys = f'{str(rstats["keys.count"])}⚿'
        redis_mem = strfbytes(rstats["dataset.bytes"])

        await ctx.send(f'redis: {redis_mem} | {redis_keys} | {redis_time}')

    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command()
    async def ping(self, ctx: commands.Context):
        await self._ping(ctx)

    @channelwise(checkfun=bot_channel_only)
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command()
    async def redis(self, ctx: commands.Context):
        await self._redis(ctx)

    @channelwise(checkfun=bot_channel_only)
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command()
    async def fullping(self, ctx: commands.Context):
        await self._ping (ctx)
        await self._redis(ctx)
