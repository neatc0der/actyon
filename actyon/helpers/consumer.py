from asyncio.tasks import gather
from inspect import iscoroutinefunction
from logging import Logger
from typing import Generic, List, Type, TypeVar, get_args

from actyon.exceptions import ConsumerError
from actyon.hook import HookEventType

from .common import FunctionWrapper, WrapperCollection, filter_results
from .log import get_logger


log: Logger = get_logger()

T = TypeVar("T")


class Consumer(Generic[T], FunctionWrapper):
    __orig_class__: Type

    def verify(self) -> None:
        if len(self._signature.parameters) == 0:
            raise ConsumerError(self, f"missing parameter for consumption: {self._func.__name__}"
                                      f" ({self._func.__module__})")

        if len(self._signature.parameters) > 1:
            raise ConsumerError(self, f"too many parameters: {self._func.__name__} ({self._func.__module__})")

        t: Type[T] = get_args(self.__orig_class__)[0]
        if next(iter(self._signature.parameters.values())).annotation is not List[t]:  # type: ignore
            raise ConsumerError(self, f"invalid parameter annotation: {self._func.__name__} ({self._func.__module__})")

        if self._signature.return_annotation is not None:
            raise ConsumerError(self, f"invalid return annotation: {self._func.__name__} ({self._func.__module__})")

        if not iscoroutinefunction(self._func):
            raise ConsumerError(self, f"consumer is not async: {self._func.__name__} ({self._func.__module__})")

    async def __call__(self, data: List[T]) -> None:
        await filter_results(await gather(self._func(data)), self.actyon, has_return=False)


class ConsumerCollection(WrapperCollection[T, Consumer]):
    async def execute(self, data: List[T]) -> None:  # type: ignore[override]
        await filter_results(await gather(
            *(consumer(data) for consumer in self._functions),
            return_exceptions=True), self.actyon, has_return=False)

        if len(self._functions) == 0:
            log.warning(f"no consumers available for this actyon: {self.actyon.name}")
            await self.actyon.send_event(HookEventType.NO_CONSUMER)
