from typing import TYPE_CHECKING

from twitchio.websocket import WSConnection
from twitchio.message import Message
from twitchio.channel import Channel
from twitchio.chatter import WhisperChatter

from core.utils.logger import get_log

if TYPE_CHECKING:
    from core.bot import Bot

logging = get_log(__name__)

class WSConnectionWrapper(WSConnection):

    # FACADE: wrapper to properly parse PONG messages and not just ignore them
    async def _process_data(self, data: str):
        groups = data.split()
        if groups[1] == 'PONG':
            parsed = {"action": "PONG", "message": groups[-1][1:]}
            partial_ = self._actions.get(parsed["action"])
            if partial_:
                await partial_(parsed)
        a = await super()._process_data(data)
        return a

    # FACADE: For my project I want to treat my bot's own messages the same way as others
    # e.g. verifying if a pyramid break was successful
    async def _privmsg_echo(self, parsed):
        logging.debug(f'ACTION: PRIVMSG(ECHO):: {parsed["channel"]}')

        channel = Channel(name=parsed["channel"], websocket=self)
        chatter = WhisperChatter(websocket=self, name=self.nick)
        message = Message(
            raw_data=parsed["data"],
            content=parsed["message"],
            author=chatter, # WHY: the FUCK was author not set for echo messages??? can't make a Context without it
            channel=channel,
            tags={},
            echo=True,
        )

        self.dispatch("message", message)

    # FACADE: Small pong dispatcher for pinging twitch puporses
    async def _pong(self, parsed):
        logging.debug(f'ACTION: PONG:: {parsed["message"]}')
        
        self.dispatch("pong", parsed)

    # FACADE: add new actions
    def initialize(self):
        self._actions["PRIVMSG(ECHO)"] = self._privmsg_echo
        self._actions["PONG"] = self._pong

def apply_websocket_patch(bot: 'Bot'):
    bot._connection.__class__ = WSConnectionWrapper
    WSConnectionWrapper.initialize(bot._connection)
