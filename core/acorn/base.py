import inspect
from typing import TYPE_CHECKING

from core.nut.nut import Nut
from core.utils.logger import get_log


if TYPE_CHECKING:
    from core.bot import Bot


class Acorn():

    _nuts: dict[str, Nut] = {}
    _name: str

    def __init__(self):
        self._name = self._name or self.__class__.__name__

    def load_nuts(self, bot: 'Bot') -> None:
        logging = get_log(self.__module__)
        for _, method in inspect.getmembers(self):
            if isinstance(method, Nut):
                details = method.register(self, bot)
                logging.info(f"Loaded <{method.__class__.__name__}> [{method.fullname}] {details}")

                self._nuts[method.fullname] = method

    def unload_nuts(self, bot) -> None:
        for fullname in self._nuts:
            bot.remove_nut(fullname)

    @property
    def name(self) -> str:
        return self._name
