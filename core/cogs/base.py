import inspect
from typing import TYPE_CHECKING

from twitchio.ext import commands

from core.decorators.invoker import Invoker

if TYPE_CHECKING:
    from core.bot import Bot

class BaseCog(commands.Cog):

    _bot: 'Bot'
    _invocations: dict[str, Invoker] = {}

    def __init__(self, bot: 'Bot'):
        self._bot = bot

    def _load_methods(self, bot) -> None:
        for _, method in inspect.getmembers(self):
            if isinstance(method, Invoker):
                method._instance = self
                method.cog = self

                self._invocations[method.name] = method
                bot.add_invocation(method)

        super()._load_methods(bot)

    def _unload_methods(self, bot) -> None:
        for name in self._invocations:
            bot.remove_invocation(name)

        super()._load_methods(bot)
