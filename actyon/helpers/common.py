from inspect import Signature, signature
from logging import Logger
from typing import Any, Callable, Generic, Iterable, List, TypeVar, Union

import actyon
from actyon.exceptions import ConsumerError, ProducerError
from actyon.hook import HookEventType
from .log import get_logger


log: Logger = get_logger()


class ActyonChild:
    def __init__(self, actyon: "actyon.Actyon") -> None:
        self._actyon = actyon

    @property
    def actyon(self) -> "actyon.Actyon":
        return self._actyon


# todo: refactor these classes
class FunctionWrapper(ActyonChild):
    def __init__(self, actyon: "actyon.actyon.Actyon", func: Callable[..., Any]) -> None:
        super().__init__(actyon)
        self._func: Callable[..., Any] = func
        self._signature: Signature = signature(func)

    @property
    def name(self) -> str:
        return self._func.__name__

    @property
    def module(self) -> str:
        return self._func.__module__

    def verify(self) -> None:
        raise NotImplementedError()


F = TypeVar('F', bound=FunctionWrapper)
T = TypeVar('T')


async def filter_results(returns: Iterable[Union[List[T], BaseException]], actyon: "actyon.Actyon",
                         has_return: bool = True) -> List[List[T]]:
    results: List[List[T]] = [r for r in returns if not isinstance(r, BaseException)]
    exceptions: List[BaseException] = [r for r in returns if isinstance(r, BaseException)]

    if any(exceptions):
        await actyon.send_event(HookEventType.FAIL)

    if has_return:
        if not any(results):
            await actyon.send_event(HookEventType.PRELIMINARY_EMPTY)
        elif any(r for r in results if len(r) > 0 and (len(r) > 1 or not isinstance(r[0], list) or len(r[0]) > 0)):
            await actyon.send_event(HookEventType.RESULT_PRODUCED)

    for exc in exceptions:
        if isinstance(exc, ConsumerError):
            log.exception(f"an error occurred while running consumer: {exc.consumer.name} ({exc.consumer.module})",
                          exc_info=exc)

        elif isinstance(exc, ProducerError):
            log.exception(f"an error occurred while running procuder: {exc.producer.name} ({exc.producer.module})",
                          exc_info=exc)

        else:
            log.exception("unexpected error during execution", exc_info=exc)

    return results


class WrapperCollection(Generic[T, F], ActyonChild):
    def __init__(self, actyon: "actyon.Actyon") -> None:
        super().__init__(actyon)
        self._functions: List[F] = []

    @property
    def actyon(self) -> "actyon.Actyon":
        return self._actyon

    def add(self, func: F) -> None:
        func.verify()
        self._functions.append(func)

    async def execute(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def __len__(self) -> int:
        return len(self._functions)
