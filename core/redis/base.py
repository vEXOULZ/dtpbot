from abc import ABC

from redis_om import (
    get_redis_connection,
    Field,
    HashModel,
    Migrator
)

from core.config import REDIS_URL

redis = get_redis_connection(url=REDIS_URL, db=0)

class BaseModel(HashModel, ABC):
    class Meta:
        global_key_prefix = "dtp-bot"
        database = redis

Migrator().run()
