import datetime as dt
import inspect
from typing import List, Optional, Tuple, Union

from twitchio.ext import commands
from twitchio.message import Message

from core.cogs.meta import MetaCog
from core.cogs.pyramid import PyramidCog
from core.patches.http import apply_http_patch
from core.patches.websocket import apply_websocket_patch
from core.redis.auths import BotAuths
from core.redis.settings import ActiveChannels
from core.utils.logger import get_log
from core.decorators.invoker import Invoker

logging = get_log(__name__)

class Bot(commands.Bot):

    start_time: dt.datetime
    _invocations: dict[str, Invoker] = {}
    channels: ActiveChannels

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...

        auths = BotAuths.get()
        self.channels = ActiveChannels.get()
        logging.info("Initial channels: %s", str(self.channels.active_channels))
        super().__init__(
            token            = auths.token,
            client_secret    = auths.client_secret,
            prefix           = '^',
            initial_channels = self.channels.active_channels
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

        self.add_cog(MetaCog(self))
        self.add_cog(PyramidCog(self))

    async def join_channels(self, channels: Union[List[str], Tuple[str]]):
        joined = self.channels.join(channels)
        if len(joined) > 0:
            logging.info("joining channels: %s", str(joined))
            await super().join_channels(joined)

    async def part_channels(self, channels: Union[List[str], Tuple[str]]):
        parted = self.channels.part(channels)
        if len(parted) > 0:
            logging.info("parting channels: %s", str(parted))
            await super().part_channels(parted)

    async def event_message(self, message: Message):
        # removes echo check
        await self.handle_commands(message)

    async def invoke(self, context: commands.Context):
        for cog in self._invocations.values():
            await cog(context)
        if context.message.echo:
            return
        if not context.prefix or not context.is_valid:
            return
        self.run_event("command_invoke", context)
        await context.command(context)

    def add_cog(self, cog: commands.Cog):
        super().add_cog(cog)
        # if isinstance(cog, HasInvocation):
            # self._invokable_cogs[cog.name] = cog
        logging.info('cog <%s> loaded', cog.name)

    def remove_cog(self, cog_name: str):
        # if cog_name in self._invokable_cogs:
            # self._invokable_cogs.pop(cog_name)
        super().remove_cog(cog_name)
        logging.info('cog <%s> unloaded', cog_name)

    def add_invocation(self, invocation: Invoker):
        """Method which registers a command for use by the bot.

        Parameters
        ------------
        command: :class:`.Command`
            The command to register.
        """
        if not isinstance(invocation, Invoker):
            raise TypeError("Invocations passed must be a subclass of Invoker.")
        elif invocation.name in self._invocations:
            raise commands.TwitchCommandError(
                f"Failed to load command <{invocation.name}>, am invocation with that name already exists."
            )
        elif not inspect.iscoroutinefunction(invocation._callback):
            raise commands.TwitchCommandError(f"Failed to load invocation <{invocation.name}>. Invocations must be coroutines.")
        self._invocations[invocation.name] = invocation

    def get_invocation(self, name: str) -> Optional[Invoker]:
        return self._invocations.get(name, None)

    def remove_invocation(self, name: str):
        try:
            del self._invocations[name]
        except KeyError as e:
            raise commands.CommandNotFound(f"The invocation '{name}` was not found", name) from e

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'World {ctx.author.name}!')
