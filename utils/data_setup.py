from sqlalchemy.orm import Session

from core.database.auths import BotAuths
from core.database.sql import engine

auths = BotAuths(
    user_id       = '12314',
    client_id     = 'abcdefghijklmnopqrstuvwxyz0123',
    client_secret = 'abcdefghijklmnopqrstuvwxyz0123',
    token         = 'abcdefghijklmnopqrstuvwxyz0123',
    refresh_token = 'abcdefghijklmnopqrstuvwxyz0123456789abcdefghijkl5g',
)
with Session(engine) as session:
    session.add(auths)
    session.commit()

