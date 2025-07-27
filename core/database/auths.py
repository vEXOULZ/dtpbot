from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from core.database.sql import Base, create_session

class AuthMissing(Exception): ...

class BotAuths(Base):
    __tablename__ = "bot_auths"

    user_id      : Mapped[str] = mapped_column(primary_key=True)
    client_id    : Mapped[str]
    client_secret: Mapped[str]
    token        : Mapped[str]
    refresh_token: Mapped[str]

    @classmethod
    def get(cls, user_id: str) -> 'BotAuths':
        with create_session() as session:
            res = session.get(BotAuths, ident=user_id)
            if res is None:
                raise AuthMissing()
            return res

    def save(self):
        with create_session() as session:
            session.add(self)
            session.commit()
