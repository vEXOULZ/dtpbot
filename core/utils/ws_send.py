from typing import Callable

from core.config import ENVIRONMENT

def build_appender(env) -> Callable:
    if env == 'dev':
        def privmsg(content: str):
            if content.startswith('/'):
                split = content.split(' ', 1)
                return f"{split[0]} 🔧 {split[-1] if len(split) == 2 else ''}"
            return f"🔧 {content}"
    else:
        def privmsg(content: str):
            return content
    return privmsg

beauty: Callable = build_appender(ENVIRONMENT)
