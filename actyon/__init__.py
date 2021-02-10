import inspect
from logging import Logger
from typing import Any, Callable, List, Type

from .actyon import Actyon, ActyonError
from .console import DisplayHook  # noqa: F401
from .helpers.log import get_logger as _get_logger
from .hook import ActyonHook, HookEvent, HookEventType  # noqa: F401


_log: Logger = _get_logger()


async def execute(name: str, obj: Any) -> None:
    actyon: Actyon = Actyon.get(name)
    if actyon is None:
        raise ActyonError(f"unknown actyon: {actyon}")

    try:
        await actyon.execute(obj)
    except ActyonError as e:
        _log.exception(str(e))


def produce(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def _inner(func: Callable[..., Any]) -> Callable[..., Any]:
        t: Type = inspect.signature(func).return_annotation
        actyon: Actyon = Actyon.get_or_create('name', t)
        return actyon.producer(func)

    if name is None or not isinstance(name, str):
        raise ActyonError("invalid use of @produce: provide name")

    return _inner


def consume(name: str) -> Callable[[Callable[[List[Any]], None]], Callable[[List[Any]], None]]:
    def _inner(func: Callable[..., Any]) -> Callable[..., Any]:
        t: Type = next(iter(inspect.signature(func).parameters.values())).annotation \
                  if len(inspect.signature(func).parameters) > 0 else None
        actyon: Actyon = Actyon.get_or_create('name', t)
        return actyon.consumer(func)

    if name is None or not isinstance(name, str):
        raise ActyonError("invalid use of @consume: provide name")

    return _inner
