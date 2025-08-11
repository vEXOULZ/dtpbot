from typing import TYPE_CHECKING
from functools import wraps

from twitchio.http import TwitchHTTP
from twitchio.errors import AuthenticationError
import aiohttp

from core.database.auths import BotAuths
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


    @wraps(TwitchHTTP._generate_login)
    async def _generate_login(self):
        redirecter = await super()._generate_login()
        # self.auths.client_id     = self.client_id # NOTE should never change
        self.auths.client_secret = self.client_secret
        self.auths.refresh_token = self._refresh_token
        self.auths.token         = self.token
        self.auths.save()
        self.client._connection._token = self.token # TODO: do this in a nicer way
        return redirecter
    
    # WHY didnt it check for closed connections??
    # trying to keep the same connection alive for days is wild
    def check_session(self):
        if   not self.session    : logging.info("No session found: new aiotthp client session created")
        # elif self.session.closed : logging.info("Session closed: new aiotthp ClientSession created")
        else                     : return
        self.session = aiohttp.ClientSession()

    # WHY didnt it check for closed connections??
    @wraps(TwitchHTTP.request)
    async def request(self, *args, **kwargs):
        self.check_session()
        return await super().request(*args, **kwargs)

    # WHY didnt it check for closed connections??
    @wraps(TwitchHTTP._generate_login)
    async def _generate_login(self, *args, **kwargs):
        self.check_session()
        return await super()._generate_login(*args, **kwargs)

    # WHY didnt it check for closed connections??
    @wraps(TwitchHTTP.validate)
    async def validate(self, *, token: str = None) -> dict:
        self.check_session()
        try:
            data = await super().validate(token=token)
        except AuthenticationError:
            # WHY: if I can regenerate login, why not do it?
            await self._generate_login()
            data = await super().validate(token=self.token)
        return data

def apply_http_patch(bot: 'Bot', auths: BotAuths):
    bot._http = TwitchHTTPWrapper(bot, auths = auths)
