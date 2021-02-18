import inspect
from asyncio.tasks import gather
from logging import Logger
from typing import Any, Callable, Iterable, List, Optional, Type

from .actyon import Actyon, ActyonError
from .console import DisplayHook  # noqa: F401
from .helpers.log import get_logger as _get_logger
from .hook import ActyonHook, HookEvent, HookEventType  # noqa: F401


_log: Logger = _get_logger()


async def execute(*names: str, dependency: Any) -> None:
    actyons: List[Actyon] = []
    for name in names:
        actyon: Optional[Actyon] = Actyon.get(name)
        if actyon is None:
            raise ActyonError(f"unknown actyon: {name}")
        actyons.append(actyon)

    if len(names) == 0:
        raise ActyonError("no actyon name provided")

    results: Iterable[Any] = await gather(*(actyon.execute(dependency) for actyon in actyons), return_exceptions=True)
    for i, exc in enumerate(results):
        if isinstance(exc, BaseException):
            _log.exception(f"error while executing {actyons[i].name}", exc_info=exc)


def produce(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def _inner(func: Callable[..., Any]) -> Callable[..., Any]:
        t: Type = inspect.signature(func).return_annotation
        actyon: Actyon = Actyon.get_or_create(name, t)
        return actyon.producer(func)

    if name is None or not isinstance(name, str):
        raise ActyonError("invalid use of @produce: provide name")

    return _inner


def consume(name: str) -> Callable[[Callable[[List[Any]], None]], Callable[[List[Any]], None]]:
    def _inner(func: Callable[..., Any]) -> Callable[..., Any]:
        t: Type = next(iter(inspect.signature(func).parameters.values())).annotation \
            if len(inspect.signature(func).parameters) > 0 else None
        actyon: Actyon = Actyon.get_or_create(name, t)
        return actyon.consumer(func)

    if name is None or not isinstance(name, str):
        raise ActyonError("invalid use of @consume: provide name")

    return _inner
