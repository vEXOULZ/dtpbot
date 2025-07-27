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

    #                       quoted arg (\" quote esc) | named par | regular arg
    _parsing_commands_regex = r"""((?<!\\)".*?(?<!\\)")|(-\S+.*?)|(\S+.*?)"""
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
                    if parameter is not None:
                        # TODO throw error
                        pass
                    else:
                        parameter = r[1]

        return args, kwargs

    def admin_kwargs(self, ctx: commands.Context, **kwargs):

        if '_ch' in kwargs:
            new_channel = copy.copy(ctx.channel)
            new_channel._name = kwargs.pop('_ch')
            ctx.channel = new_channel

        return ctx, kwargs

    async def __call__(self, ctx: commands.Context, *args, **kwargs):

        if len(arguments := ctx.message.content.split(' ', 1)) == 2:
            matches = re.findall(self._parsing_commands_regex, arguments[1])
            nargs, nkwargs = self._reorganize_findall(matches)
            args += tuple(nargs)
            kwargs |= nkwargs

        ctx, kwargs = self.admin_kwargs(ctx, **kwargs)

        return await super().__call__(ctx, *args, **kwargs)

    def register(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.add_command_nut(self)

    def unregister(self, acorn: 'Acorn', bot: 'Bot'):
        self.acorn = acorn
        bot.remove_command_nut(self)