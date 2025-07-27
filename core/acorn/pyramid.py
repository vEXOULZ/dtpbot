from random import random
import math

from twitchio.ext import commands
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String, Column, select, update

from core.acorn.base import Acorn
from core.nut.nut import Nut, CommandNut
from core.nut.restrictions import restrict, PRIVILEDGE, fullname_only
from core.utils.logger import get_log
from core.database.sql import Base, create_session

logging = get_log(__name__)

default_facts = [
    "In geometry, pyramids have triangular sides that come together at the top (apex).",
    #{}"If they have 4 sides and a square base they are called a square pyramid.",
    "If they have 4 FACES, 3 SIDES AND A TRIANGULAR BASE, they are called a tetrahedron.",
    "Humans have been building structures using pyramid shapes for thousands of years.",
    #"The first pyramid type structures are believed to have been built by the Mesopotamians around 5000 years ago. These structures were called ziggurats. Pyramid type structures found in Caral, Peru also date back to around this time.",
    "Ancient Egyptian pyramids are the most well known pyramid structures.",
    "Most Ancient Egyptian pyramids were built as tombs for Pharaohs and their families.",
    "Over 130 pyramids have been discovered in Egypt.",
    "The first Egyptian pyramid is believed to be the Pyramid of Djoser, it was built in Saqqara around 4650 years ago (2640 BC).",
    "The Great Pyramid of Giza is the oldest and largest of three pyramids in the Giza Necropolis.",
    "Also known as the Pyramid of Khufu, it is the oldest of the Ancient Wonders of the World and the last one still largely intact.",
    "Most Aztec and Mayan pyramids were step pyramids with temples on top.",
    #{}"The Mayan civilization stretched from Southern Mexico the northern part of Central America.",
    "Mayan pyramids date back to around 3000 years ago.",
    "Aztec pyramids in central Mexico date back to around 600 years ago.",
    #"El Castillo (also known as the Temple of Kukulkan) is perhaps the most famous Mayan pyramid. Located in the archaeological site of Chichen Itza, in the Mexican state of Yucatan, it is a popular tourist destination with over 1 million visitors every year.",
    "The world's largest pyramid by volume is the Great Pyramid of Cholula in Puebla, Mexico.",
    "Sudan is home to a large number of Nubian pyramids which are smaller and steeper than those found in Egypt.",
    #"Although Greeks aren’t known for their pyramid building, a number of pyramid like structures do exist, with the best known being the Pyramid of Hellinikon.",
    "Pyramids were built in China to house the remains of some early Chinese emperors.",
    "The Roman Empire built a number of pyramids including the Pyramid of Cestius in Rome, Italy which still stands today.",
    "Not all pyramids are ancient, there are also a large number of modern structures that share the famous pyramid shape.",
    "The Louvre in Paris is home to a large glass pyramid.",
    "The Palace of Peace and Reconciliation in Astana, Kazakhstan is a 62 metre (203 feet) high pyramid.",
    "The 30 story Luxor Hotel in Las Vegas is a large pyramid that holds over 4000 rooms.",
    "The Slovak Radio Building in Bratislava, Slovakia is shaped like an inverted (upside down) pyramid.",
    "Saqqara is a huge ancient burial ground built near the Egyptian city of Memphis.",
    "Also known as the Pyramid of Khufu, it is the oldest of the Ancient Wonders of the World and the last one still largely intact.",
    "For over 3800 years, the Great Pyramid of Giza was the tallest man made structure in the world.",
    "As well as Giza and Saqqara, important Egyptian Pyramid sites include Dashur, Abusir, Meidum, Lisht, Abu Rawash and others.",
    "Nearly all Egyptian Pyramids are located on the west bank of the Nile.",
    "Egyptian Pyramids often contain multiple chambers and passages.",
    #"One tomb that was left largely intact was that of Tutankhamun in the Valley of the Kings. Rediscovered in 1922 by Howard Carter, this famous tomb is best known for the solid gold funerary mask of Tutankhamun.",
    "The Pyramid of Menkaure, the Pyramid of Khafre and the Great Pyramid of Khufu are precisely aligned with the Constellation of Orion.",
    "The base of the Great Pyramid of Giza covers 55,000 m2 (592,000 ft 2) with each side greater than 20,000 m2 (218,000 ft2) in area.",
    #"The interior temperature inside the Great Pyramid of Giza is constant and equals the average temperature of the earth, 20 Degrees Celsius (68 Degrees Fahrenheit).",
    "The four faces of the Great Pyramid of Giza are slightly concave, the only pyramid to have been built this way.",
    "Shungite pyramids are said to possess numerous effects, such as EMF protection, healing properties and energy balancing.",
]

def count(str1):
    obj = {}
    for el in str1.split(" "):
        obj[el] = obj.get(el, 0) + 1
    return obj

class PyramidData(Base):
    __tablename__ = "acorn_pyramid_data"

    user_name : Mapped[str] = mapped_column(primary_key=True)
    active    : Mapped[bool]
    profile   : Mapped[str]
    facts                   = Column(ARRAY(String))

    @classmethod
    def generate_default(cls, user_name):
        new_data = PyramidData(
            user_name = user_name,
            active = False,
            profile = 'kind',
            facts = default_facts
        )
        with create_session() as session:
            session.add(new_data)
            session.commit()

    @classmethod
    def get_data(cls, user_name) -> list[str]:
        def query():
            with create_session() as session:
                stmt = select(PyramidData).where(PyramidData.user_name == user_name)
                result = session.execute(stmt)
                data = result.one_or_none()
                if data is not None: data = data[0]
            return data
        
        data = query()
        if data is None:
            cls.generate_default(user_name)
            data = query()
        return data


class PyramidProfiles(Base):
    __tablename__ = "acorn_pyramid_profile"

    profile_name : Mapped[str] = mapped_column(primary_key=True)
    up           : Mapped[float]
    upx          : Mapped[float]
    down         : Mapped[float]
    downx        : Mapped[float]

    @classmethod
    def get_all(cls) -> list[str]:
        with create_session() as session:
            stmt = select(PyramidProfiles)
            result = session.execute(stmt)
            data = result.all()

        return {x[0].profile_name: x[0] for x in data}

class PyramidAcorn(Acorn):

    _name = 'pyramid'
    active = {}
    last_user = {}
    last_message = {}
    level = {}
    max_level = {}
    pyramid = {}
    configs: dict[str, PyramidData] = {}
    profiles = PyramidProfiles.get_all()
    last_fact = {}
    req_level = 3

    def get_random_fact(self, ctx: commands.Context):
        rolled = self.last_fact.get(ctx.channel.name)
        while rolled == self.last_fact.get(ctx.channel.name):
            rolled = math.floor(random() * len(self.configs[ctx.channel.name].facts))
        self.last_fact[ctx.channel.name] = rolled
        return self.configs[ctx.channel.name].facts[rolled]

    def reset_pyramid(self, ctx: commands.Context, user, msg):
        self.last_user   [ctx.channel.name] = user
        self.last_message[ctx.channel.name] = msg
        self.level       [ctx.channel.name] = 0
        self.max_level   [ctx.channel.name] = 0
        self.pyramid     [ctx.channel.name] = ''

    async def test_pyramid(self, ctx: commands.Context):
        channel = ctx.channel.name
        user    = ctx.author.name
        message = ctx.message.content

        # different chatter
        if user != self.last_user[channel]:
            if self.level[channel] >= 2:
                logging.info(f"#{channel} | {self.last_user[channel]}'s '{self.pyramid[channel]}' pyramid lvl {str(1)}/{str(1)} destroyed by '{user}: {self.last_message[channel]}'")
            return self.reset_pyramid(ctx, user, message)

        # try to detect pyramid if no ongoing pyramid
        if self.level[channel] == 0:
            new_words = count(message)
            old_words = count(self.last_message[channel])
            for x, y in new_words.items():
                # NOTE: DETECTED PYRAMID at lvl 2
                if y == 2 and x in old_words and old_words[x] == 1:
                    self.level[channel] = self.max_level[channel] = y
                    self.pyramid[channel] = x
                    logging.info(f"#{channel} | '{x}' pyramid lvl {str(1)}/{str(1)} on '{user}: {self.last_message[channel]}'")
                    logging.info(f"#{channel} | '{x}' pyramid lvl {str(self.level[channel])}/{str(self.max_level[channel])} on '{user}: {message}'")
                    return
            return self.reset_pyramid(ctx, user, message)

        occurences = len(message.split(self.pyramid[channel])) - 1
        dif = occurences - self.level[channel]

        # pyramid goes up by one (and was at highest point)
        if dif == 1 and self.level[channel] == self.max_level[channel]:
            self.level[channel] = self.max_level[channel] = occurences
            logging.info(f"#{channel} | '{self.pyramid[channel]}' pyramid lvl {str(self.level[channel])}/{str(self.max_level[channel])} on '{user}: {message}'")
            if self.roll(channel, self.configs[channel].profile, self.level[channel], True):
                return await self.facts_over_feelings(ctx, self.get_random_fact(ctx))
            return

        # pyramid goes down by one (and achieved required max height)
        if dif == -1 and self.max_level[channel] >= self.req_level:
            self.level[channel] = occurences
            logging.info(f"#{channel} | '{self.pyramid[channel]}' pyramid lvl {str(self.level[channel])}/{str(self.max_level[channel])} on '{user}: {message}'")
            if self.level[channel] == 1: # at bottom (successful)
                await self.feelings_won_over(ctx, user, self.max_level[channel], self.pyramid[channel])
                return self.reset_pyramid(ctx, user, message)
            else:
                if self.roll(channel, self.configs[channel].profile, self.level[channel], False):
                    return await self.facts_over_feelings(ctx, self.get_random_fact(ctx))
            return

        return self.reset_pyramid(ctx, user, message)

    def roll(self, channel: str, profile: str, level: int, up: bool) -> bool:
        roll = random()
        bs = self.profiles[profile].up  if up else self.profiles[profile].down
        xs = self.profiles[profile].upx if up else self.profiles[profile].downx
        threshold = bs + ((level-1) * xs)
        logging.info(f"#{channel} | rolled {roll} vs {threshold} ({bs} + (({level} - 1) * {xs})")
        return roll > threshold

    async def facts_over_feelings(self, ctx: commands.Context, fact: str):
        await ctx.send(f"/me ▲ FACT: {fact}")

    async def feelings_won_over(self, ctx: commands.Context, user: str, level: int, pyramid: str):
        logging.info(f"#{ctx.channel.name} | complete '{pyramid}' pyramid lvl {str(level)} by {user}")
        await ctx.send(f"/me ▲ GRATS @{user}: {str(level)} high {pyramid} Clap")

    @Nut
    async def invoice(self, ctx: commands.Context):
        if ctx.channel.name not in self.configs:
            self.reset_pyramid(ctx, '', '')
            self.configs[ctx.channel.name] = PyramidData.get_data(ctx.channel.name)

        if self.configs[ctx.channel.name].active:
            await self.test_pyramid(ctx)

    @fullname_only
    @CommandNut
    @restrict(PRIVILEDGE.MODERATOR)
    async def setprofile(self, ctx: commands.Context, profile: str):
        if profile not in self.profiles.keys():
            # TODO throw error
            return

        if ctx.channel.name not in self.configs:
            self.reset_pyramid(ctx, '', '')
            self.configs[ctx.channel.name] = PyramidData.get_data(ctx.channel.name)

        config = self.configs[ctx.channel.name]
        config.profile = profile
        config.save()
        logging.info(f"#{ctx.channel.name} | pyramid destroying profile changed to '{profile}' by @{ctx.author.name}")
        await ctx.send(f"dooming profile changed to '{profile}'")

    @fullname_only
    @CommandNut
    @restrict(PRIVILEDGE.MODERATOR)
    async def enable(self, ctx: commands.Context):
        if ctx.channel.name not in self.configs:
            self.reset_pyramid(ctx, '', '')
            self.configs[ctx.channel.name] = PyramidData.get_data(ctx.channel.name)

        config = self.configs[ctx.channel.name]
        config.active = True
        config.save()
        logging.info(f"#{ctx.channel.name} | pyramid destroying enabled by @{ctx.author.name}")
        await ctx.send(f"Pyramid watch enabled")

    @fullname_only
    @CommandNut
    @restrict(PRIVILEDGE.MODERATOR)
    async def disable(self, ctx: commands.Context):
        if ctx.channel.name not in self.configs:
            self.reset_pyramid(ctx, '', '')
            self.configs[ctx.channel.name] = PyramidData.get_data(ctx.channel.name)

        config = self.configs[ctx.channel.name]
        config.active = False
        config.save()
        logging.info(f"#{ctx.channel.name} | pyramid destroying disabled by @{ctx.author.name}")
        await ctx.send(f"No longer watching for pyramids")

    @fullname_only
    @CommandNut
    @restrict(PRIVILEDGE.GOD)
    async def refreshprofiles(self, ctx: commands.Context):
        self.profiles = PyramidProfiles.get_all()
        logging.info(f"#{ctx.channel.name} | profile values refreshed by @{ctx.author.name}")
        await ctx.send(f"Profiles refreshed; available: {list(self.profiles.keys())}")


