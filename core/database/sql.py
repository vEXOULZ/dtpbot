from typing import Iterable

from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy import create_engine, update

from core.config import SQLALCHEMY

engine = create_engine(SQLALCHEMY)

def create_session():
    return Session(engine)

class Base(DeclarativeBase):

    def to_dict(self):
        return {x: y for x, y in self.__dict__.items() if x[0] != '_'}

    def save(self):
        with create_session() as session:
            stmt = update(self.__class__)
            session.execute(stmt, [self.to_dict()])
            session.commit()

    def create(self):
        with create_session() as session:
            session.add(self)
            session.commit()

    @classmethod
    def bulk_save(cls, objs: 'Iterable[Base]'):
        with create_session() as session:
            stmt = update(objs[0].__class__)
            session.execute(stmt, [o.to_dict() for o in objs])
            session.commit()
