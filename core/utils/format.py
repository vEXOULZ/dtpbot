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


def parse_escape_characters(string: str) -> str:

    result = []
    i = 0
    while True:
        idx = string.find('\\', i)

        if idx == -1: # no more escapes; add remainder
            result.append(string[i:])
            break

        result.append(string[i:idx]) # add everything up to next escape

        if idx == len(string) - 1: # last character is an escape character; so end it (nothing to add)
            break

        result.append(string[idx+1]) # addnext character (e.g. 'b' in '\b')
        i = idx+2 # skips 2 (the escape and escapee) (e.g '\b')

    return ''.join(result)