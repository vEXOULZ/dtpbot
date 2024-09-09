from twitchio.ext import commands

from core.cogs.base import BaseCog
from core.decorators.invoker import invocable
from core.utils.logger import get_log

logging = get_log(__name__)

def count(str1):
    obj = {}
    for el in str1.split(" "):
        obj[el] = obj.get(el, 0) + 1
    return obj

class PyramidCog(BaseCog):

    def get_random_fact(self):
        rolled = self.last_fact
        while rolled == self.last_fact:
            rolled = floor(random() * len(self.facts))
        self.last_fact = rolled
        return self.facts[rolled]

    def reset_pyramid(self, user, msg):
        self.last_user = user
        self.last_message = msg
        self.level = 0
        self.max_level = 0
        self.req_level = 0

    def test_pyramid(self, context: commands.Context):
        if msg.user == self.last_user:
            if self.level == 0:
                new_words = count(msg.message)
                old_words = count(self.last_message)
                for x, y in new_words.items():
                    if (y == 2 or y == 3) and x in old_words and old_words[x] == 1:
                        self.level = y
                        self.max_level = y
                        self.req_level = y + 1
                        self.pyramid = x
                        logging.info(f"[{msg.channel}] !!! '{x}' pyramid lvl {str(1)} on '{msg.user}: {self.last_message}'")
                        logging.info(f"[{msg.channel}] !!! '{x}' pyramid lvl {str(self.level)} on '{msg.user}: {msg.message}'")
                        return ('NOTHING', )
            else:
                test = msg.message.split(self.pyramid)
                dif = abs(self.level - (len(test) - 1))
                if dif != 1:
                    self.reset_pyramid(msg.user, msg.message)
                    return ('NOTHING', )
                if len(test) >= self.level + 2 and self.level == self.max_level:
                    self.level = len(test) - 1
                    self.max_level = self.level
                    logging.info(f"[{msg.channel}] !!! '{self.pyramid}' pyramid lvl {self.level} on '{msg.user}: {msg.message}'")
                    roll = random()
                    threshold = profiles[self.profile]['up'] + ((self.level-1) * profiles[self.profile]['upx'])
                    logging.info(f"[{msg.channel}] !!! rolled '{roll}' vs {threshold}'")
                    if roll > threshold:
                        return ('FACT', self.get_random_fact())
                    return ('NOTHING', )
                elif self.level > 0 and len(test) <= self.level + 1:
                    self.level = len(test) - 1
                    logging.info(f"{msg.channel}] !!! '{self.pyramid}' pyramid lvl${self.level} on '{msg.user}: {msg.message}'")
                    if self.level == 1:
                        if self.max_level >= self.req_level:
                            logging.info(f"[{msg.channel}] !!! complete '{self.pyramid}' pyramid lvl {self.max_level} by {msg.user}")
                            ret = f"/me grats @{msg.user} - {self.max_level} high {self.pyramid} ▲ Clap"
                            self.reset_pyramid(msg.user, msg.message)
                            return ('GRATS', ret)
                    elif self.level < 1:
                        self.reset_pyramid(msg.user, msg.message)
                        return ('NOTHING', )
                    else:
                        roll = random()
                        threshold = profiles[self.profile]['down'] + ((self.level-1) * profiles[self.profile]['downx'])
                        logging.info(f"[{msg.channel}] !!! rolled '{roll}' vs {threshold}'")
                        if roll > threshold:
                            return ('FACT', self.get_random_fact())
                        else:
                            return ('NOTHING', )
        self.reset_pyramid(msg.user, msg.message)
        return ('NOTHING', )

    @invocable()
    async def invoice(self, context: commands.Context):
        # pyramided = self.test_pyramid(context)
        # match pyramided:
        #     case ('NOTHING', ):
        #         pass
        #     case ('FACT', x):
        #         await context.send(f"/me ▲ FACT: {x}")
        #     case ('GRATS', x):
        #         await context.send(x)
        pass
