from typing import Callable
import traceback

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

def one_line_exception(e: Exception) -> str:
    locale, reason = traceback.format_exception(e)[-2:]
    locale = locale.split("\n")[0] # location only
    return f"{locale.strip()} ▲ {reason.strip()}"