from typing import Iterable

from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy import create_engine, update
from sqlalchemy.dialects.postgresql import insert

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

    def create_or_update(self):
        with create_session() as session:
            data = self.to_dict()
            stmt = insert(self.__class__).values(data).on_conflict_do_update(constraint=self.__table__.primary_key, set_=data)
            session.execute(stmt)
            session.commit()

    @classmethod
    def bulk_update(cls, objs: 'Iterable[Base]'):
        with create_session() as session:
            stmt = update(objs[0].__class__).values([o.to_dict() for o in objs])
            session.execute(stmt)
            session.commit()

    @classmethod
    def bulk_create_or_update(cls, objs: 'Iterable[Base]'):
        with create_session() as session:
            data = [o.to_dict() for o in objs]
            stmt = insert(objs[0].__class__).values(data).on_conflict_do_update(constraint=cls.__table__.primary_key, set_=data)
            session.execute(stmt)
            session.commit()
