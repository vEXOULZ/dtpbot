import datetime as dt
from typing import List, Tuple, Union
import re

from twitchio.ext.commands import Context
from twitchio.message import Message
from twitchio.client import Client

from core.acorn.base import Acorn
from core.acorn.meta import MetaAcorn
from core.acorn.pyramid import PyramidAcorn
from core.patches.http import apply_http_patch
from core.patches.websocket import apply_websocket_patch
from core.database.auths import BotAuths
from core.database.settings import Channels
from core.utils.logger import get_log
from core.nut.nut import Nut, CommandNut
from core.config import ENVIRONMENT, GITHASH, GITSUMMARY , GITWHEN
from core.utils.ws_send import beauty

logging = get_log(__name__)

class Bot(Client):

    start_time: dt.datetime
    channels: list[str]
    _acorns: dict[str, Acorn] = {}
    _command_nuts: dict[str, CommandNut] = {}
    _invoke_nuts: list[Nut] = []
    _command_prefix = "🏜️"
    _dev_prefix = "_"

    def __init__(self, user_id: str):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...

        auths = BotAuths.get(user_id)
        self.channels = Channels.get_active_channels()
        logging.info("Initial channels: %s", str(self.channels))
        super().__init__(
            token            = auths.token,
            client_secret    = auths.client_secret,
            initial_channels = self.channels
        )
        apply_http_patch(self, auths)
        apply_websocket_patch(self)

    def run(self):
        self.start_time = dt.datetime.now()
        super().run()

    async def event_ready(self):
        logging.info('Logged in as | %s', self.nick)
        logging.info('User id is | %s', self.user_id)

        await self.join_channels([self.nick])

        self.add_acorn(MetaAcorn(self))
        self.add_acorn(PyramidAcorn())

        alive_notif = f"I am alive! build {GITHASH} as of {GITWHEN} \"{GITSUMMARY}\""
        await self._connection.send(f"PRIVMSG #{self.nick} :{beauty(alive_notif)}\r\n")

    async def join_channels(self, channels: Union[List[str], Tuple[str]]):
        joined = []
        for channel in channels:
            if channel not in self.channels:
                self.channels.append(channel)
                Channels.add(channel)
                joined.append(channel)
        if len(joined) > 0:
            logging.info("joining channels: %s", str(joined))
            await super().join_channels(joined)

    async def part_channels(self, channels: Union[List[str], Tuple[str]]):
        parted = []
        for channel in channels:
            if channel in self.channels:
                Channels.part(channel)
                parted.pop(channel)
        if len(parted) > 0:
            logging.info("parting channels: %s", str(parted))
            await super().part_channels(channels)

    async def event_message(self, message: Message):
        # removes echo check
        ctx = Context(message, self)

        nutting_list = []

        if ENVIRONMENT == 'dev': # dev only
            if not ctx.message.content.startswith(self._dev_prefix) and ctx.author.name != self.nick:
                return
            ctx.message.content = ctx.message.content[len(self._dev_prefix):].strip()
        elif ctx.channel.name == self.nick and ctx.message.content.startswith(self._dev_prefix):
            return # prod sybau if in bot channel and dev prefix is used

        # command nuts
        if ctx.message.content.startswith(self._command_prefix):
            split = ctx.message.content[len(self._command_prefix):].strip().split(' ', 1)
            kword = split[0]
            content = ''
            if len(split) == 2:
                content = split[1]
            ctx.message.content = content

            if kword in self._command_nuts:
                nutting_list.append(self._command_nuts[kword](ctx))

        # invoke nuts
        for nut in self._invoke_nuts:
            nutting_list.append(nut(ctx))

        for nut in nutting_list:
            await nut

    def add_acorn(self, acorn: Acorn):
        if isinstance(acorn, Acorn):
            acorn.load_nuts(self)
            self._acorns[acorn.name] = acorn
        logging.info('acorn <%s> loaded', acorn.name)

    def remove_acorn(self, acorn_name: str):
        if acorn_name in self._acorns:
            acorn = self._acorns.pop(acorn_name)
            acorn.unload_nuts(self)
        logging.info('acorn <%s> unloaded', acorn_name)

    def add_nut(self, nut: Nut):
        self._invoke_nuts.append(nut)

    def remove_nut(self, nut: Nut):
        self._invoke_nuts.pop(nut)

    def add_command_nut(self, nut: CommandNut):
        """Method which registers a command for use by the bot.

        Parameters
        ------------
        command: :class:`.Command`
            The command to register.
        """
        if not isinstance(nut, Nut):
            raise TypeError("Nuts must be a subclass of Nut.")
        elif not nut._fullname_only and nut.name in self._command_nuts:
            logging.warning(f"Nut <{nut.fullname}> overrode <{self._command_nuts[nut.name].fullname}>.")
        self._command_nuts[nut.fullname] = nut
        if not nut._fullname_only:
            self._command_nuts[nut.name] = nut

    def remove_command_nut(self, fullname: str | CommandNut):
        if isinstance(fullname, CommandNut):
            fullname = fullname.fullname
        try:
            if fullname in self._command_nuts:
                nut = self._command_nuts[fullname]
                if not nut._fullname_only and self._command_nuts[nut.name].fullname == fullname:
                    del self._command_nuts[nut.name]
                del self._command_nuts[fullname]
        except KeyError as e:
            raise KeyError(f"The nut '{fullname}' was not found") from e

