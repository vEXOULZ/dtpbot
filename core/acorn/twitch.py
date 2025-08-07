import uuid
import asyncio
import datetime as dt
from typing import TYPE_CHECKING
import os
from copy import copy

import psutil
from twitchio.ext import commands
from twitchio.errors import HTTPException

from core.utils.ws_send import beauty
from core.acorn.base import Acorn
from core.utils.logger import get_log
from core.utils.timeit import TimeThis
from core.utils.units import strfdelta, strfbytes
from core.nut.nut import CommandNut, DEFAULT_ALIAS, CronNut
from core.nut.result import Result, ECODE
from core.nut.restrictions import cooldown, PRIVILEDGE, channel, restrict, get_priviledge
from core.config import BOTNAME
from twitchio import Channel

if TYPE_CHECKING:
    from core.bot import Bot

logging = get_log(__name__)

class TwitchAcorn(Acorn):

    _name = 'twitch'

    @CommandNut()
    async def streaminfo(self, ctx: commands.Context, channel: str = None):
        if channel == None:
            channel = ctx.channel.name
        result = await ctx.bot.fetch_streams(user_logins=[channel])
        if len(result) == 0:
            return Result(ECODE.OK, f"#{channel} is not live at the moment")
        return Result(ECODE.OK, f"#{channel} is live ▲ '{result[0].game_name}' ▲ {strfdelta(dt.datetime.now(tz=dt.timezone.utc) - result[0].started_at)} ▲ {str(result[0].viewer_count)} viewers ▲ title: {result[0].title}")


    @CommandNut()
    async def schedule(self, ctx: commands.Context, channel: str = None):
        if channel == None:
            channel = ctx.channel.name
        channel_id = await ctx.bot.fetch_users(names = [channel])
        try:
            result = await ctx.bot._http.get_channel_schedule(broadcaster_id=channel_id[0].id)
        except HTTPException:
            return Result(ECODE.OK, f"#{channel} does not have a schedule at the moment")
        stream = result['data']['segments'][0]
        return Result(ECODE.OK, f"#{channel}'s next stream is in {strfdelta(dt.datetime.fromisoformat(stream['start_time']) - dt.datetime.now(tz=dt.timezone.utc))} ({stream['start_time']}): {stream['title']}")
