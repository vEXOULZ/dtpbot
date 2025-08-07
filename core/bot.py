import datetime as dt
from typing import List, Tuple, Union, Collection
from asyncio import as_completed

from twitchio.ext.commands import Context
from twitchio.message import Message
from twitchio.client import Client

from core.acorn.base import Acorn
from core.acorn.meta import MetaAcorn
from core.acorn.pyramid import PyramidAcorn
from core.acorn.twitch import TwitchAcorn
from core.patches.http import apply_http_patch
from core.patches.websocket import apply_websocket_patch
from core.patches.context import new_context
from core.database.auths import BotAuths
from core.database.settings import Channels
from core.utils.logger import get_log
from core.nut.nut import CommandNut, RegexNut
from core.nut.result import Result, ECODE
from core.config import ENVIRONMENT, GITHASH, GITSUMMARY , GITWHEN
from core.utils.format import beauty, one_line_exception

logging = get_log(__name__)

class Bot(Client):

    start_time: dt.datetime
    channels: list[str]
    _acorns: dict[str, Acorn] = {}
    _command_nuts: dict[str, CommandNut] = {}
    _regex_nuts: list[RegexNut] = []
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
        self.add_acorn(TwitchAcorn())

        ctx = new_context(self)
        await self.sendprivmsg(ctx, f"I am alive! build {GITHASH} as of {GITWHEN} \"{GITSUMMARY}\"")

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
                parted.append(channel)
        if len(parted) > 0:
            logging.info("parting channels: %s", str(parted))
            await super().part_channels(channels)

    async def event_message(self, message: Message):
        # removes echo check
        ctx = Context(message, self)

        nutting_list = []

        ctx.original_content = ctx.message.content

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
                nutting_list.append(self._command_nuts[kword].actuate(ctx))

        # regex nuts
        for nut in self._regex_nuts:
            nutting_list.append(nut.actuate(ctx))

        for nut in as_completed(nutting_list):
            result = await nut
            await self.treat_result(ctx, result)

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

    def add_regex_nut(self, nut: RegexNut):
        self._regex_nuts.append(nut)

    def remove_regex_nut(self, nut: RegexNut):
        self._regex_nuts.pop(nut)

    def add_command_nut(self, nut: CommandNut, aliases: list[str] = None):
        """Method which registers a command for use by the bot.

        Parameters
        ------------
        command: :class:`.Command`
            The command to register.
        """

        assert(aliases is not None)

        if not isinstance(nut, CommandNut):
            raise TypeError("command nut must be a subclass of CommandNut.")

        for alias in aliases:
            if alias in self._command_nuts:
                logging.warning(f"Nut <{nut.fullname}> overrode <{self._command_nuts[nut.name].fullname}> on alias <{alias}>.")
            self._command_nuts[alias] = nut

    def remove_command_nut(self, nut: CommandNut, aliases: list[str] = None):

        assert(aliases is not None)

        for alias in aliases:
            if alias in self._command_nuts:
                if self._command_nuts[alias].fullname is not nut.fullname:
                    # TODO error
                    continue
                del self._command_nuts[alias]

    async def treat_result(self, ctx: Context, result: Result):
        if isinstance(result, Result):
            match result.code:
                case ECODE.OK:
                    await self.sendprivmsg(ctx, result.result)
                case ECODE.SILENT:
                    pass
                case ECODE.ERROR:
                    logging.warning(f"#{ctx.channel.name} @{ctx.author.name}: {ctx.original_content} ▲ {result.code} {result.code.name} ▲ {one_line_exception(result.result)}")
                    await self.sendprivmsg(ctx, str(result.result))
                case _:
                    logging.error(f"#{ctx.channel.name} @{ctx.author.name}: {ctx.original_content} ▲ {result.code} {result.code.name} ▲ {one_line_exception(result.result)}")
        else:
            logging.error(f"#{ctx.channel.name} @{ctx.author.name}: {ctx.original_content} ▲ no Result object ▲ {result}")

    async def sendprivmsg(self, ctx: Context, message: str | Collection[str]):
        if isinstance(message, str):
            await ctx.send(beauty(message))
        else:
            for msg in message:
                await ctx.send(beauty(msg))