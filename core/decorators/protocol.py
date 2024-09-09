from typing import Protocol, Callable, runtime_checkable

@runtime_checkable
class NestedCommand(Protocol):
    _callback: Callable
