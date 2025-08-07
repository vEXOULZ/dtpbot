from enum import IntEnum

class ECODE(IntEnum):
    UNCAUGHT = -2
    ERROR    = -1
    OK       = 0
    SILENT   = 1


class Result():

    __slots__ = ("_code", "_result")

    def __init__(self, code: ECODE, result: str | Exception = None):
        self._code      = code
        self._result    = result

    @property
    def code(self) -> ECODE:
        return self._code

    @property
    def result(self) -> str | Exception:
        return self._result
