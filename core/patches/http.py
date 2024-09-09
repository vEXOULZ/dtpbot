from typing import TYPE_CHECKING

from twitchio.http import TwitchHTTP
from twitchio.errors import AuthenticationError

from core.redis.auths import BotAuths
from core.utils.logger import get_log

if TYPE_CHECKING:
    from core.bot import Bot

logging = get_log(__name__)

class TwitchHTTPWrapper(TwitchHTTP):

    def __init__(self, *args, auths: BotAuths, **kwargs):
        super().__init__(
            *args,
            api_token     = auths.token,
            client_secret = auths.client_secret,
            client_id     = auths.client_id,
            **kwargs
        )
        self.auths          = auths
        self._refresh_token = auths.refresh_token # WHY: not exactly sure why I can't create a bot with a refresh token

    async def validate(self, *, token: str = None) -> dict:
        # WHY: if I can regenerate login, why not do it?
        try:
            data = await super().validate(token=token)
        except AuthenticationError:
            await self._generate_login()
            data = await super().validate(token=self.token)
        return data

    async def _generate_login(self):
        redirecter = await super()._generate_login()
        self.auths.client_id     = self.client_id
        self.auths.client_secret = self.client_secret
        self.auths.refresh_token = self._refresh_token
        self.auths.token         = self.token
        self.auths.save()
        self.client._connection._token = self.token # TODO: do this in a nicer way
        return redirecter

def apply_http_patch(bot: 'Bot', auths: BotAuths):
    bot._http = TwitchHTTPWrapper(bot, auths = auths)
