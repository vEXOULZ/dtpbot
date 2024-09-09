from typing import Callable, TypeVar
import inspect

from twitchio.ext.commands import Context

class Invoker:
    def __init__(self, name: str, func: Callable, **attrs) -> None:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Command callback must be a coroutine.")
        self._callback = func
        self._checks = []
        self._cooldowns = []
        self._name = name

        self._instance = None
        self.cog = None

        try:
            self._checks.extend(func.__checks__)  # type: ignore
        except AttributeError:
            pass
        try:
            self._cooldowns.extend(func.__cooldowns__)  # type: ignore
        except AttributeError:
            pass
        sig = inspect.signature(func)
        self.params = sig.parameters.copy()  # type: ignore

        self.event_error = None
        self._before_invoke = None
        self._after_invoke = None
        self.no_global_checks = attrs.get("no_global_checks", False)

        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value.replace(annotation=eval(value.annotation, func.__globals__))  # type: ignore

    @property
    def name(self) -> str:
        return '.'.join([self.cog.name, self._name])

    async def invoke(self, context: Context, *args, **kwargs) -> None:
        async def try_run(func, *, to_command=False):
            try:
                await func
            except Exception as _e:
                if not to_command:
                    context.bot.run_event("error", _e)
                else:
                    context.bot.run_event("command_error", context, _e)

        await try_run(self._callback(self, context))

    async def __call__(self, context: Context, *, index=0) -> None:
        await self.invoke(context, index=index)

I = TypeVar("I", bound="Invoker")

def invocable(
    *, name: str = None, cls: type[I] = Invoker
) -> Callable[[Callable], I]:
    if cls and not inspect.isclass(cls):
        raise TypeError(f"cls must be of type <class> not <{type(cls)}>")

    def decorator(func: Callable) -> I:
        fname = name or func.__name__
        return cls(
            name=fname,
            func=func,
        )

    return decorator