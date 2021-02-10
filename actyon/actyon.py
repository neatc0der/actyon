from logging import Logger
from typing import Any, Callable, Dict, Generic, List, Type, TypeVar, Union

from typing_extensions import get_args

from .exceptions import ActyonError
from .helpers.consumer import Consumer, ConsumerCollection
from .helpers.injector import Injector
from .helpers.log import get_logger
from .helpers.producer import Producer, ProducerCollection
from .hook import ActyonHook, HookEvent, HookEventType


log: Logger = get_logger()

T = TypeVar("T")


class Actyon(Generic[T]):
    all: Dict[str, "Actyon"] = {}

    def __init__(self, name: str, **options: Dict[str, Any]) -> None:
        if name in Actyon.all:
            raise ActyonError(f"actyon already exists: {name}")
        self._name: str = name
        self._producers: ProducerCollection[T] = ProducerCollection[T](self)
        self._consumers: ConsumerCollection[T] = ConsumerCollection[T](self)
        self._hook: ActyonHook = options.get("hook")

        if isinstance(options.get("consumer"), Callable):
            self.producer(options.get("consumer"))

        if isinstance(options.get("producer"), Callable):
            self.producer(options.get("producer"))

        self.all[self.name] = self

    @property
    def name(self) -> str:
        return self._name

    @property
    def producers(self) -> ProducerCollection[T]:
        return self._producers

    @property
    def consumers(self) -> ConsumerCollection[T]:
        return self._consumers

    @classmethod
    def get(cls, name: str) -> "Actyon":
        return cls.all.get(name)

    @classmethod
    def get_or_create(cls, name: str, t: Type) -> "Actyon":
        if name not in cls.all:
            return Actyon[t](name)

        return cls.get(name)

    async def send_event(self, event_type: HookEventType) -> None:
        if self._hook is not None:
            await self._hook.event(HookEvent(actyon=self, type=event_type))

    async def execute(self, obj: Union[Any, Injector]) -> None:
        await self.send_event(HookEventType.START)
        injector: Injector
        if isinstance(obj, Injector):
            injector = obj
        else:
            injector = Injector(obj)

        data: List[T] = await self.producers.execute(injector)
        await self.send_event(HookEventType.AFTER_PRODUCE)
        await self.consumers.execute(data)
        await self.send_event(HookEventType.END)

    async def _consume(self, data: List[T]) -> None:
        for consumer in self._consumers:
            try:
                consumer(data)
            except Exception:
                log.exception(f"an error occurred while running consumer: {consumer.name} ({consumer.module})")

    def consumer(self, func: Callable[[List[T]], None] = None) -> Callable[[List[T]], None]:
        def _inner(f: Callable[[List[T]], None]) -> Callable[[List[T]], None]:
            t: Type = get_args(self.__orig_class__)[0]
            consumer: Consumer = Consumer[t](self, func)
            self.consumers.add(consumer)
            return f

        if func is not None:
            return _inner(func)

        return _inner

    def producer(self, func: Callable[..., Any] = None) -> Callable[..., Any]:
        def _inner(f: Callable[..., Any]) -> Callable[..., Any]:
            t: Type = get_args(self.__orig_class__)[0] if hasattr(self, "__orig_class__") else None
            producer: Producer = Producer[t](self, func)
            self.producers.add(producer)
            return f

        if func is not None:
            return _inner(func)

        return _inner
