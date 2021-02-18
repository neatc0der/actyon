from asyncio import gather
from inspect import Signature, iscoroutinefunction
from logging import Logger
from typing import Any, Callable, Dict, Generic, List, Type, TypeVar, cast, get_args

import actyon
from actyon.exceptions import ProducerError
from actyon.hook import HookEventType

from .common import FunctionWrapper, WrapperCollection, filter_results
from .injector import Injector
from .log import get_logger


log: Logger = get_logger()

T = TypeVar("T")


class Producer(Generic[T], FunctionWrapper):
    __orig_class__: Type

    def __init__(self, actyon: "actyon.actyon.Actyon", func: Callable[..., Any], **options: Dict[str, Any]) -> None:
        super().__init__(actyon, func)
        self._custom_validator: Callable[[Signature], None] = cast(Callable, options.get("validator"))

    def verify(self) -> None:
        if any(p for p in self._signature.parameters.values() if p.annotation.__name__ == "_empty"):
            raise ProducerError(self, f"at least one parameter was not annotated: {self._func.__name__}"
                                      f" ({self._func.__module__})")

        if len(self._signature.parameters) != len(set(p.annotation for p in self._signature.parameters.values())):
            raise ProducerError(self, f"at least one parameter annotation is not unique: {self._func.__name__} "
                                      f"({self._func.__module__})")

        t: Type = get_args(self.__orig_class__)[0]
        if self._signature.return_annotation not in (t, List[t]):  # type: ignore
            raise ProducerError(self, f"return annotation needs to be {t.__name__} or List[{t.__name__}]: "
                                      f"{self._func.__name__} ({self._func.__module__})")

        if not iscoroutinefunction(self._func):
            raise ProducerError(self, f"producer is not async: {self._func.__name__} ({self._func.__module__})")

        if self._custom_validator is not None:
            self._custom_validator(self._signature)

    def required(self) -> List[str]:
        return [
            p.annotation.name
            for p in self._signature.parameters.values()
        ]

    async def __call__(self, injector: Injector) -> List[List[T]]:
        return await filter_results(
            await gather(
                *injector.inject_to(self._func),
                return_exceptions=True,
            ),
            self.actyon,
        )


class ProducerCollection(WrapperCollection[T, Producer]):
    async def execute(self, injector: Injector) -> List[T]:  # type: ignore[override]
        results: List[List[List[T]]] = await filter_results(
            await gather(
                *(producer(injector) for producer in self._functions),
                return_exceptions=True
            ),
            self.actyon,
        )

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
