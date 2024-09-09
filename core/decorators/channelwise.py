from typing import Callable, TypeVar, TYPE_CHECKING

from twitchio.ext import commands

from core.decorators.protocol import NestedCommand

if TYPE_CHECKING:
    from core.cogs.base import BaseCog

C = TypeVar("C")

def channelwise(whitelist: list[str] = None, blacklist: list[str] = None, checkfun: Callable = None) -> Callable[[Callable], C]:
    def decorator(func: NestedCommand) -> C:
        if not isinstance(func, NestedCommand):
            raise TypeError("Command must be of Nested Command type to be decorated")
        original = func._callback
        async def runner(self: 'BaseCog', ctx: commands.Context, *args, **kwargs):
            if (whitelist is not None and ctx.channel.name in whitelist):
                return await original(self, ctx, *args, **kwargs)
            if (blacklist is not None and ctx.channel.names not in blacklist):
                return await original(self, ctx, *args, **kwargs)
            if (checkfun is not None and checkfun(self, ctx, *args, **kwargs)):
                return await original(self, ctx, *args, **kwargs)
            return
        func._callback = runner
        return func

    return decorator

def bot_channel_only(self: 'BaseCog', ctx: commands.Context, *args, **kwargs):
    return self._bot.nick == ctx.channel.name
