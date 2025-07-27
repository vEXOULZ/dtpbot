import inspect
from typing import TYPE_CHECKING

from core.nut.nut import Nut

if TYPE_CHECKING:
    from core.bot import Bot


class Acorn():

    _nuts: dict[str, Nut] = {}
    _name: str

    def __init__(self):
        self._name = self._name or self.__class__.__name__

    def load_nuts(self, bot: 'Bot') -> None:
        for _, method in inspect.getmembers(self):
            if isinstance(method, Nut):
                method.register(self, bot)

                self._nuts[method.fullname] = method

    def unload_nuts(self, bot) -> None:
        for fullname in self._nuts:
            bot.remove_nut(fullname)

    @property
    def name(self) -> str:
        return self._name
