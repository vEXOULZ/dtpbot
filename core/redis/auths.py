from core.redis.base import redis

class RedisAuthMissing(Exception): ...

CLIENT_ID     = 'client_id'
CLIENT_SECRET = 'client_secret'
TOKEN         = 'token'
REFRESH_TOKEN = 'refresh_token'

_all_keys = [
    CLIENT_ID    ,
    CLIENT_SECRET,
    TOKEN        ,
    REFRESH_TOKEN,
]

class BotAuths():
    client_id    : str
    client_secret: str
    token        : str
    refresh_token: str

    _singleton: 'BotAuths | None' = None

    def _set_from_redis(self, key: str) -> None:
        setattr(self, key, redis.get(key))

    @classmethod
    def get(cls) -> 'BotAuths':
        if BotAuths._singleton is not None:
            return BotAuths._singleton
        auths   = cls()
        BotAuths._singleton = auths

        missing = []
        for key in _all_keys:
            auths._set_from_redis(key)
            if getattr(auths, key) is None:
                missing.append(key)

        if len(missing):
            raise RedisAuthMissing(f"<{'>, <'.join(missing)}> key{'s are' if len(missing) > 2 else '  is'} missing in REDIS server")

        return auths

    def save(self) -> None:
        pipe = redis.pipeline()
        pipe.set(CLIENT_ID    , self.client_id    )
        pipe.set(CLIENT_SECRET, self.client_secret)
        pipe.set(TOKEN        , self.token        )
        pipe.set(REFRESH_TOKEN, self.refresh_token)
        pipe.execute()
