from core.redis.base import redis
from core.utils.logger import get_log

logging = get_log(__name__)

ACTIVE_CHANNELS = 'active_channels'

class ActiveChannels():
    active_channels: set

    _singleton: 'ActiveChannels | None' = None

    def join(self, channels: list[str]) -> list[str]:
        joined = []
        for channel in channels:
            if channel not in self.active_channels:
                joined.append(channel)
                self.active_channels.add(channel)
        if len(joined) > 0:
            pipe = redis.pipeline()
            for channel in joined:
                pipe.sadd(ACTIVE_CHANNELS, channel)
                logging.info("redis added channel %s", channel)
            pipe.execute()
        return joined

    def part(self, channels: list[str]) -> list[str]:
        # TODO add expiry time (2 weeks?) for all parted channel data
        parted = []
        for channel in channels:
            if channel in self.active_channels:
                parted.append(channel)
                self.active_channels.remove(channel)
        if len(parted) > 0:
            pipe = redis.pipeline()
            for channel in parted:
                pipe.srem(ACTIVE_CHANNELS, channel)
                logging.info("redis removed channel %s", channel)
            pipe.execute()
        return parted

    @classmethod
    def get(cls) -> 'ActiveChannels':
        if ActiveChannels._singleton is not None:
            return ActiveChannels._singleton
        auths   = cls()
        ActiveChannels._singleton = auths

        auths.active_channels = redis.smembers(ACTIVE_CHANNELS) or set()

        return auths
