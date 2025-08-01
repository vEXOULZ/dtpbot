from typing import Callable, TYPE_CHECKING
import inspect
import re
import copy

from twitchio.ext import commands

if TYPE_CHECKING:
    from core.acorn.base import Acorn
    from core.bot import Bot

class Nut():

    _callback: Callable = None
    _acorn: 'Acorn' = None

    def __init__(self, fun: Callable, *args, name: str = None, **kwargs):
        if not inspect.iscoroutinefunction(fun):
            raise TypeError("Command callback must be a coroutine.")
        self._callback = fun
        self._name = name or fun.__name__

    async def __call__(self, ctx: commands.Context, *args, **kwargs):
        return await self._callback(self.acorn, ctx, *args, **kwargs)

    @classmethod
    def apply(cls, fun: 'Nut | Callable', *args, **kwargs):
        if isinstance(fun, Nut):
            return fun
        return cls(fun, *args, **kwargs)

    def register(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.add_nut(self)

    def unregister(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.remove_nut(self)

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

class CommandNut(Nut):

    #                       quoted arg (\" quote esc)  | named par       | regular arg
    _parsing_commands_regex = r"""((?<!\\)".*?(?<!\\)")|(-[a-zA-z]\S*.*?)|(\S+.*?)"""
    _fullname_only = False

    _transforms = [
        lambda x: x[1:-1].replace(r'\"', '"'), # 0 - quoted arg
        lambda x: x[1:],                       # 1 - named par
        lambda x: x,                           # 2 - regular arg
    ]

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
            new_channel = copy.copy(ctx.channel)
            new_channel._name = kwargs.pop('_ch')
            ctx.channel = new_channel

        if '_sybau' in kwargs:
            sybau = kwargs.pop('_sybau')
            if sybau:
                async def do_nothing(*a, **k): return
                ctx.send = do_nothing

        return ctx, kwargs

    async def __call__(self, ctx: commands.Context, *args, **kwargs):

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

        return await super().__call__(ctx, *args, **kwargs)

    def register(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.add_command_nut(self)

    def unregister(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.remove_command_nut(self)