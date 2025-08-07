from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy import String, Column, select

from core.utils.logger import get_log
from core.database.sql import Base, create_session

logging = get_log(__name__)

class Channels(Base):
    __tablename__ = "joined_channels"

    user_name  : Mapped[str]  = mapped_column(primary_key=True)
    user_id    : Mapped[str]  = mapped_column(nullable=True)
    active     : Mapped[bool] = mapped_column()
    ambassators               = Column(ARRAY(String))
    settings                  = Column(JSONB())

    live: bool = False

    @classmethod
    def add(cls, user_name) -> str:

        channel = Channels(
            user_name = user_name
        )
        channel.create()
        return user_name

    @classmethod
    def part(self, user_name) -> str:
        # TODO add expiry time (2 weeks?) for all parted channel data
        Channels(
            user_name = user_name
        ).delete()
        return user_name


    @classmethod
    def get_active_channels(cls) -> str:
        with create_session() as session:
            stmt = select(Channels)
            result = session.execute(stmt)
            return [channel[0].user_name for channel in result.all()]
