from typing import TYPE_CHECKING
from copy import copy

from twitchio.ext import commands
from twitchio.message import Message
from twitchio.chatter import PartialChatter
from twitchio.channel import Channel

if TYPE_CHECKING:
    from core.bot import Bot

def switch_channel(ctx: commands.Context, channel_name: str) -> commands.Context:
    new_channel = copy(ctx.channel)
    new_channel._name = channel_name
    ctx.channel = new_channel
    return ctx

def new_context(bot: "Bot", channel_name: str = None) -> commands.Context:
    if channel_name is None:
        channel_name = bot.nick
    return commands.Context(
        Message(
            tags = {
                'id': f'HELP',
                'tmi-sent-ts': None
            },
            author = PartialChatter(bot._connection, name=bot.nick),
            channel = Channel(name=channel_name, websocket=bot._connection)
        ), bot
    )