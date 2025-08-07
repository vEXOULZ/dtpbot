from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String, Column, select

from core.utils.logger import get_log
from core.database.sql import Base, create_session

logging = get_log(__name__)

class Channels(Base):
    __tablename__ = "joined_channels"

    user_name: Mapped[str] = mapped_column(primary_key=True)

    @classmethod
    def add(cls, user_name) -> list[str]:

        channel = Channels(
            user_name = user_name
        )
        channel.create()
        return user_name

    @classmethod
    def part(self, user_name) -> list[str]:
        # TODO add expiry time (2 weeks?) for all parted channel data
        Channels(
            user_name = user_name
        ).delete()
        return user_name


    @classmethod
    def get_active_channels(cls) -> list[str]:
        with create_session() as session:
            stmt = select(Channels)
            result = session.execute(stmt)
            return [channel[0].user_name for channel in result.all()]
