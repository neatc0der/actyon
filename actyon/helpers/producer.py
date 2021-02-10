from asyncio import gather
from inspect import iscoroutinefunction
from logging import Logger
from typing import Generic, List, Type, TypeVar

from typing_extensions import get_args

from actyon.exceptions import ProducerError
from actyon.hook import HookEventType
from .common import FunctionWrapper, WrapperCollection, filter_results
from .injector import Injector
from .log import get_logger


log: Logger = get_logger()

T = TypeVar("T")


class Producer(Generic[T], FunctionWrapper):
    def verify(self) -> None:
        if any(p for p in self._signature.parameters.values() if p.annotation.__name__ == "_empty"):
            raise ProducerError(self, f"at least one parameter was not annotated: {self._func.__name__}" +
                                " ({self._func.__module__})")

        if len(self._signature.parameters) != len(set(p.annotation for p in self._signature.parameters.values())):
            raise ProducerError(self, f"at least one parameter annotation is not unique: {self._func.__name__} " +
                                "({self._func.__module__})")

        t: Type = get_args(self.__orig_class__)[0]
        if self._signature.return_annotation is not List[t]:
            raise ProducerError(self, f"invalid return annotation: {self._func.__name__} ({self._func.__module__})")

        if not iscoroutinefunction(self._func):
            raise ProducerError(self, f"producer is not async: {self._func.__name__} ({self._func.__module__})")

    def required(self) -> List[str]:
        return [
            p.annotation.name
            for p in self._signature.parameters.values()
        ]

    async def __call__(self, injector: Injector) -> List[T]:
        return await filter_results(await gather(
            *injector.inject_to(self._func),
            return_exceptions=True,
        ), self.actyon)


class ProducerCollection(WrapperCollection[T, Producer]):
    async def execute(self, injector: Injector) -> List[T]:
        results: List[List[T]] = await filter_results(await gather(
            *(producer(injector) for producer in self._functions),
            return_exceptions=True), self.actyon)

        if len(self._functions) == 0:
            log.warning(f"no producers available for this actyon: {self.actyon.name}")
            await self.actyon.send_event(HookEventType.NO_PRODUCER)

        elif len(results) == 0:
            log.error(f"no dependencies available for this actyon: {self.actyon.name}")
            await self.actyon.send_event(HookEventType.FAIL)

        return [
            o
            for p in results
            for r in p
            for o in r
        ]
