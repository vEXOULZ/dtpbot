import datetime as dt
from typing import TYPE_CHECKING

from twitchio.ext import commands
from twitchio.errors import HTTPException

from core.acorn.base import Acorn
from core.utils.logger import get_log
from core.utils.units import strfdelta
from core.nut.nut import CommandNut
from core.nut.result import Result, ECODE

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
