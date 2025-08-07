from typing import Callable, TYPE_CHECKING
import inspect
import re
from enum import Enum, auto
from abc import ABC
from functools import wraps
from itertools import chain

from zoneinfo import ZoneInfo
import aiocron
from twitchio.ext import commands
from twitchio.ext.commands import Context

from core.nut.error import ParameterParseException, DtpReturnableException
from core.patches.context import switch_channel
from core.utils.format import parse_escape_characters
from core.utils.logger import get_log
from core.nut.result import Result, ECODE
from core.patches.context import new_context
from core.nut.restrictions import get_priviledge, PRIVILEDGE

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
            result = await self.trigger(self.acorn, ctx, *args, **kwargs)
            if isinstance(result, Result):
                return result
            return Result(ECODE.MALFORMED, result)
        except DtpReturnableException as e:
            return Result(ECODE.ERROR, e)
        except Exception as e:
            return Result(ECODE.UNCAUGHT, e)

    async def trigger(self, acorn, ctx, *args, **kwargs):
        return await self._callback(acorn, ctx, *args, **kwargs)

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

class RegexNut(Nut):
    _regex: str = None

    def __init__(self, regex: str = r"""(?s).*""", **kwargs):
        self._regex = regex

        def wrapper(fun):
            @wraps(fun)
            async def run(acorn, ctx: Context, *args, **kwargs):
                if (match:=re.search(self._regex, ctx.message.content)) is not None:
                    return await fun(acorn, ctx, *args, match=match, **kwargs)

            return run

        self.trigger = wrapper(self.trigger)

    def register(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.add_regex_nut(self)
        return ""

    def unregister(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.remove_regex_nut(self)


class DEFAULT_ALIAS(Enum):
    BOTH_NAMES    = auto()
    FULLNAME_ONLY = auto()
    NAME_ONLY     = auto()

class CommandNut(Nut):

    #                            quoted arg (\ esc chr)   | named par       | regular arg
    _parsing_commands_regex = r"""(".*?[^\\](?:\\\\)*(?=")")|(-[a-zA-z]\S*.*?)|(\S+.*?)"""
    _aliases: list[str] = None
    _default_aliases: DEFAULT_ALIAS = DEFAULT_ALIAS.BOTH_NAMES

    def __init__(self, aliases: list[str] = None, default_aliases: DEFAULT_ALIAS = DEFAULT_ALIAS.BOTH_NAMES, **kwargs):
        self._aliases = aliases
        self._default_aliases = default_aliases

        def wrapper(fun):
            @wraps(fun)
            async def run(acorn, ctx: Context, *args, **kwargs):
                matches = re.findall(self._parsing_commands_regex, ctx.message.content)
                args, kwargs, awargs = self._reorganize_findall(matches)

                ctx = self.admin_kwargs(ctx, **awargs)

                iterargs = iter(args)
                new_args = []

                all_missing = []

                subject = next(iterargs, None)
                for name, argument in inspect.signature(self._callback).parameters.items():
                    if name in ("self", "ctx"): continue
                    cast = (lambda x: x) if argument.annotation is inspect._empty else argument.annotation
                    match argument.kind:
                        case argument.POSITIONAL_ONLY:
                            if subject is None:
                                all_missing.append(name)
                            else:
                                new_args.append(subject)
                                subject = next(iterargs, None)
                        case argument.VAR_POSITIONAL: # TODO maybe cast this somehow?
                            while subject is not None and not isinstance(subject, tuple):
                                new_args.append(cast(subject))
                                subject = next(iterargs, None)
                            continue
                        case argument.POSITIONAL_OR_KEYWORD:
                            if subject is not None:
                                new_args.append(cast(subject))
                                subject = next(iterargs, None)
                            elif name in kwargs.keys():
                                kwargs[name] = cast(kwargs[name])
                            elif argument.default is inspect._empty:
                                all_missing.append(name)
                        case argument.KEYWORD_ONLY:
                            if name in kwargs.keys():
                                kwargs[name] = cast(kwargs[name])
                        case argument.VAR_KEYWORD: # TODO cast this somehow?
                            pass # they are already there, no action is needed

                if len(all_missing) > 0:
                    raise ParameterParseException(f"'{self.fullname}' missing required positional parameter(s) {str(all_missing)}")

                args = tuple(new_args)
                return await fun(acorn, ctx, *args, **kwargs)

            return run

        self.trigger = wrapper(self.trigger)

    def _reorganize_findall(self, arguments):
        res = []
        for arg in arguments:
            res.append(next((x, parse_escape_characters(y)) for x, y in enumerate(arg) if y != ''))

        args = []
        kwargs = {}

        parameter = None
        had_parameter = False
        for argtype, argvalue in res:
            match argtype:
                case 0 | 2: # quoted arg | regular arg
                    value = argvalue
                    if argtype == 0: # quoted arg
                        value = value[1:-1] # remove quotes
                    if parameter is not None:
                        kwargs[parameter] = value
                        parameter = None
                    elif had_parameter:
                        raise ParameterParseException()
                    else:
                        args.append(value)
                case 1: # named par
                    value = argvalue[1:] # remove dash
                    parameter = value
                    kwargs[parameter] = True # for bool args
                    had_parameter = True

        awargs = {x: kwargs.pop(x) for x in list(kwargs.keys()) if x.startswith("_")} # admin args

        return args, kwargs, awargs

    def admin_kwargs(self, ctx: commands.Context, **awargs):
        if get_priviledge(ctx) < PRIVILEDGE.ADMIN:
            return ctx

        # TODO recreate context with no awargs

        if '_ch' in awargs:
            ctx = switch_channel(ctx, awargs.pop('_ch'))

        if '_sybau' in awargs:
            sybau = awargs.pop('_sybau')
            if sybau:
                async def do_nothing(*a, **k): return
                ctx.send = do_nothing

        return ctx

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
        ctx = new_context(self.bot)
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
