from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union, cast, get_args

from .exceptions import ActyonError
from .helpers.consumer import Consumer, ConsumerCollection
from .helpers.injector import Injector
from .helpers.log import get_logger
from .helpers.producer import Producer, ProducerCollection
from .hook import ActyonHook, HookEvent, HookEventType


log: Logger = get_logger()

T = TypeVar("T")


class Actyon(Generic[T]):
    __orig_class__: Type
    all: Dict[str, "Actyon"] = {}

    def __init__(self, name: str, **options: Any) -> None:
        if name in Actyon.all:
            raise ActyonError(f"actyon already exists: {name}")
        self._name: str = name
        self._producers: ProducerCollection[T] = ProducerCollection[T](self)
        self._consumers: ConsumerCollection[T] = ConsumerCollection[T](self)
        self._hook: ActyonHook = cast(ActyonHook, options.get("hook"))

        if isinstance(options.get("consumer"), Callable):  # type: ignore
            self.producer(cast(Callable, options.get("consumer")))

        if isinstance(options.get("producer"), Callable):  # type: ignore
            self.producer(cast(Callable, options.get("producer")))

        if not options.get("unregistered", False):
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
    def get(cls, name: str) -> Optional["Actyon"]:
        return cls.all.get(name)

    @classmethod
    def get_or_create(cls, name: str, t: Type, **options: Dict[str, Any]) -> "Actyon":
        a: Optional[Actyon] = cls.get(name)
        if a is None:
            a = Actyon[t](name, **options)  # type: ignore

        return a

    async def send_event(self, event_type: HookEventType) -> None:
        if self._hook is not None:
            await self._hook.event(HookEvent(action=self, type=event_type))

    async def execute(self, *objs: Union[Any, Injector]) -> None:
        await self.send_event(HookEventType.START)
        injector: Injector
        if len(objs) == 1 and isinstance(objs[0], Injector):
            injector = objs[0]
        else:
            injector = Injector(objs)

        data: List[T] = await self.producers.execute(injector)
        await self.send_event(HookEventType.AFTER_PRODUCE)
        await self.consumers.execute(data)
        await self.send_event(HookEventType.END)

    def consumer(self, func: Optional[Callable[[List[T]], Awaitable]] = None) \
            -> Union[Callable[..., Awaitable], Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]]]:
        def _inner(f: Callable[[List[T]], Awaitable]) -> Callable[[List[T]], Awaitable]:
            t: Type = get_args(self.__orig_class__)[0]
            consumer: Consumer = Consumer[t](self, f)  # type: ignore
            self.consumers.add(consumer)
            return f

        if func is not None:
            return _inner(func)

        return _inner

    def producer(self, func: Optional[Callable[..., Awaitable]] = None, **options: Any) \
            -> Union[Callable[..., Awaitable], Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]]]:
        def _inner(f: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
            t: Type = get_args(self.__orig_class__)[0] if hasattr(self, "__orig_class__") else None
            producer: Producer = Producer[t](self, f, **options)  # type: ignore
            self.producers.add(producer)
            return f

        if func is not None:
            return _inner(func)

        return _inner
