from typing import Callable, TYPE_CHECKING
import inspect
import re
import copy
from enum import Enum, auto
from abc import ABC
import datetime as dt

from zoneinfo import ZoneInfo
import aiocron
from twitchio.ext import commands
from twitchio.ext.commands import Context
from twitchio.message import Message
from twitchio.channel import Channel
from twitchio.chatter import PartialChatter

from core.patches.context import switch_channel
from core.utils.logger import get_log
from core.nut.result import Result, ECODE

logging = get_log(__name__)

if TYPE_CHECKING:
    from core.acorn.base import Acorn
    from core.bot import Bot

class Nut(ABC):

    _callback: Callable = None
    _acorn: 'Acorn' = None

    def __call__(self, fun: Callable = None, name: str = None, **kwargs):
        self.initialize_function(fun, name, **kwargs)
        return self

    async def actuate(self, ctx: commands.Context, *args, **kwargs):
        try:
            result = await self._callback(self.acorn, ctx, *args, **kwargs)
            if isinstance(result, Result):
                return result
            return Result(ECODE.UNCAUGHT, result)
        except Exception as e:
            return Result(ECODE.UNCAUGHT, e)

    def initialize_function(self, fun: Callable = None, name: str = None, **kwargs):
        if not inspect.iscoroutinefunction(fun):
            raise TypeError("Command callback must be a coroutine.")
        self._callback = fun
        self._name = name or fun.__name__
        return self

    @classmethod
    def apply(cls, fun: 'Nut | Callable', *args, **kwargs):
        if isinstance(fun, Nut):
            return fun
        return cls(fun, *args, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def fullname(self) -> str:
        return f"{self.acorn.name}.{self.name}"

    @property
    def acorn(self) -> 'Acorn':
        return self._acorn

    @acorn.setter
    def acorn(self, acc) -> None:
        self._acorn = acc

    def register(self, acorn: 'Acorn', bot: 'Bot'): ...
    def unregister(self, acorn: 'Acorn', bot: 'Bot'): ...

class InvokeNut(Nut):

    def register(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.add_invoke_nut(self)
        return ""

    def unregister(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.remove_invoke_nut(self)


class DEFAULT_ALIAS(Enum):
    BOTH_NAMES    = auto()
    FULLNAME_ONLY = auto()
    NAME_ONLY     = auto()

class CommandNut(Nut):

    #                       quoted arg (\" quote esc)  | named par       | regular arg
    _parsing_commands_regex = r"""((?<!\\)".*?(?<!\\)")|(-[a-zA-z]\S*.*?)|(\S+.*?)"""
    _aliases: list[str] = None
    _default_aliases: DEFAULT_ALIAS = DEFAULT_ALIAS.BOTH_NAMES

    _transforms = [
        lambda x: x[1:-1].replace(r'\"', '"'), # 0 - quoted arg
        lambda x: x[1:],                       # 1 - named par
        lambda x: x,                           # 2 - regular arg
    ]

    def __init__(self, aliases: list[str] = None, default_aliases: DEFAULT_ALIAS = DEFAULT_ALIAS.BOTH_NAMES, **kwargs):
        self._aliases = aliases
        self._default_aliases = default_aliases

    def _reorganize_findall(self, arguments):
        res = []
        for arg in arguments:
            res.append(next((x, self._transforms[x](y)) for x, y in enumerate(arg) if y != ''))

        args = []
        kwargs = {}

        parameter = None
        for r in res:
            match r[0]:
                case 0 | 2: # quoted arg | regular arg
                    if parameter is not None:
                        kwargs[parameter] = r[1]
                        parameter = None
                    else:
                        args.append(r[1])
                case 1: # named par
                    parameter = r[1]
                    kwargs[parameter] = True # for bool args

        return args, kwargs

    def admin_kwargs(self, ctx: commands.Context, **kwargs):

        if '_ch' in kwargs:
            ctx = switch_channel(ctx, kwargs.pop('_ch'))

        if '_sybau' in kwargs:
            sybau = kwargs.pop('_sybau')
            if sybau:
                async def do_nothing(*a, **k): return
                ctx.send = do_nothing

        return ctx, kwargs

    async def actuate(self, ctx: commands.Context, *args, **kwargs):

        if ctx.message.content != '':
            matches = re.findall(self._parsing_commands_regex, ctx.message.content)
            nargs, nkwargs = self._reorganize_findall(matches)
            args += tuple(nargs)
            kwargs |= nkwargs

        ctx, kwargs = self.admin_kwargs(ctx, **kwargs)

        casting_at = 0
        kwargs_list = list(kwargs.items())
        new_args = []
        # casting
        for name, argument in inspect.signature(self._callback).parameters.items():
            if name in ("self", "ctx"): continue
            if argument.kind == argument.VAR_POSITIONAL:
                new_args += list(args[casting_at:])
                casting_at = len(args)
                continue
            if argument.kind == argument.VAR_KEYWORD: break # all kwargs are already there
            cast = (lambda x: x) if argument.annotation is inspect._empty else argument.annotation

            if len(args) < casting_at:
                k, v = kwargs_list[casting_at - len(args)]
                kwargs[k] = cast(v)
            else:
                new_args.append(cast(args[casting_at]))
            casting_at += 1

        args = tuple(new_args)

        return await super().actuate(ctx, *args, **kwargs)

    def register(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        if self._aliases is None:
            match self._default_aliases:
                case DEFAULT_ALIAS.BOTH_NAMES:
                    self._aliases = [self.name, self.fullname]
                case DEFAULT_ALIAS.FULLNAME_ONLY:
                    self._aliases = [self.fullname]
                case DEFAULT_ALIAS.NAME_ONLY:
                    self._aliases = [self.name]
        bot.add_command_nut(self, self._aliases)
        return f"aliases = {str(self._aliases)}"

    def unregister(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.remove_command_nut(self, self._aliases)


class CronNut(Nut):

    _cronstring: str = None
    _timezone: str = None

    def __init__(self, cronstring: str, timezone: str = "UTC", **kwargs):
        self._cronstring = cronstring
        self._timezone = timezone

    async def actuate(self, *args, **kwargs):
        ctx = Context(
            Message(
                tags = {
                    'id': f'cron::{self.name}::{dt.datetime.now().isoformat()}',
                    'tmi-sent-ts': None
                },
                author = PartialChatter(self.bot._connection, name=self.bot.nick),
                channel = Channel(name=self.bot.nick, websocket=self.bot._connection)
            ), self.bot
        )
        result = await super().actuate(ctx, *args, **kwargs)
        await self.bot.treat_result(ctx, result)
        return result

    def register(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        self.bot = bot
        cronfun = aiocron.crontab(self._cronstring, func=self.actuate, start=False, tz=ZoneInfo(self._timezone))
        self.cronfun = cronfun
        self.cronfun.start()
        return self.cronfun.cronsim.explain()

    def unregister(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        self.bot = bot
        self.cronfun.stop()
        return self.cronfun.cronsim.explain()
