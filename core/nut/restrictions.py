from enum import IntEnum
from functools import wraps
import datetime as dt

from twitchio.ext import commands

from core.utils.logger import get_log
from core.nut.result import Result, ECODE

logging = get_log(__name__)


class PRIVILEDGE(IntEnum):
    PLEB = 0
    SUBSCRIBER = 1
    VIP = 2
    MODERATOR = 3
    AMBASSADOR = 4
    BROADCASTER = 5
    ADMIN = 6
    NOBODY = 7

class SCOPE(IntEnum):
    USER = 0
    CHANNEL = 1
    GLOBAL = 2

def get_priviledge(ctx: commands.Context):
    if ctx.author.name == 'vexoulz': # TODO add this to db
        return PRIVILEDGE.ADMIN
    if ctx.author.is_broadcaster:
        return PRIVILEDGE.BROADCASTER
    if ctx.author.is_mod:
        return PRIVILEDGE.MODERATOR
    if ctx.author.is_vip:
        return PRIVILEDGE.VIP
    if ctx.author.is_subscriber:
        return PRIVILEDGE.SUBSCRIBER
    return PRIVILEDGE.PLEB


def restrict(level: PRIVILEDGE):
    def deco(nut):
        from core.nut.nut import Nut
        if not isinstance(nut, Nut):
            raise TypeError("decorated object has to be nutty")

        fun = nut.trigger
        @wraps(fun)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            if get_priviledge(ctx) >= level:
                return await fun(self, ctx, *args, **kwargs)
            return Result(ECODE.SILENT, None)

        nut.trigger = wrapper
        return nut

    return deco


def cooldown(cooldown: int, exception: PRIVILEDGE = PRIVILEDGE.MODERATOR, scope: SCOPE = SCOPE.CHANNEL):
    def deco(nut):
        from core.nut.nut import Nut
        if not isinstance(nut, Nut):
            raise TypeError("decorated object has to be nutty")

        fun = nut.trigger
        @wraps(fun)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            match scope:
                case SCOPE.USER:
                    varname = f"{ctx.channel.name}.{ctx.author.name}.lastcall"
                case SCOPE.CHANNEL:
                    varname = f"{ctx.channel.name}.lastcall"
                case SCOPE.GLOBAL:
                    varname = f"lastcall"

            if varname not in nut.__dict__.keys():
                nut.__dict__[varname] = dt.datetime.min

            now = dt.datetime.now()
            if get_priviledge(ctx) >= exception or (now - nut.__dict__[varname]).total_seconds() > cooldown:
                nut.__dict__[varname] = now
                return await fun(self, ctx, *args, **kwargs)
            return Result(ECODE.SILENT, None)

        nut.trigger = wrapper
        return nut

    return deco

def channel(channels: list[str]):
    def deco(nut):
        from core.nut.nut import Nut
        if not isinstance(nut, Nut):
            raise TypeError("decorated object has to be nutty")

        fun = nut.trigger
        @wraps(fun)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            if ctx.channel.name in channels:
                return await fun(self, ctx, *args, **kwargs)
            return Result(ECODE.SILENT, None)

        nut.trigger = wrapper
        return nut

    return deco
