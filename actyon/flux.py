from asyncio import Queue, Task, create_task, gather
from copy import deepcopy
from inspect import Signature
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, Tuple, Type, TypeVar, get_args, overload

import attr
from colorama import Style

from .actyon import Actyon
from .console import ActyonState, DisplayHook, get_symbol
from .exceptions import ActyonError


class FluxError(ActyonError):
    pass


T = TypeVar("T")


class Flux(Generic[T]):
    __orig_class__: Type

    @attr.s
    class Action:
        type: str = attr.ib()
        data: Dict[str, Any] = attr.ib(factory=dict)

    def __init__(self, initial: T, unsafe: bool = False, **options: Any):
        self._store: T = initial
        self._queue: Optional[Queue[Tuple[str, Dict[str, Any]]]] = None
        self._task: Optional[Task] = None
        self._unsafe: bool = unsafe
        self._options: Dict[str, Any] = options
        self._options["unregistered"] = True
        self._actyons: Dict[str, Actyon] = {}

    @property
    def actyons(self) -> Dict[str, Actyon]:
        return self._actyons

    @property
    def state(self) -> T:
        if self._unsafe:
            return self._store
        return deepcopy(self._store)

    @state.setter
    def state(self, state: T) -> None:
        self._store = state

    def _get_or_create_actyon(self, name: str, t: Type) -> Actyon:
        a: Optional[Actyon[t]] = self._actyons.get(name)  # type: ignore
        if a is None:
            a = Actyon[t](name, **self._options)  # type: ignore
            self._actyons[name] = a

        return a

    async def run(self) -> None:
        if self._queue is None:
            self._queue = Queue()

        if self._task is not None:
            raise FluxError("flux is already running")

        self._task = create_task(self._run())

    async def _run(self) -> None:
        while self._queue:
            name, data = await self._queue.get()
            if name is None:
                raise FluxError("unable to dispatch without action type")

            actyon: Optional[Actyon] = self._actyons.get(name)
            if actyon is None:
                raise FluxError(f"unknown action: {name}")

            action: Flux.Action = Flux.Action(type=name, data=data)
            await actyon.execute(self.state, action)

            self._queue.task_done()

    async def done(self) -> None:
        if self._task is None or self._queue is None:
            raise FluxError("flux is not running")

        await self._queue.join()
        if not self._task.done:
            self._task.cancel()
            await gather(self._task, return_exceptions=True)

        self._task = None

    async def dispatch(self, name: str, **data: Dict[str, Any]) -> None:
        if self._queue is None:
            raise FluxError("flux needs to run before dispatch is executed")

        await self._queue.put((name, data))

    @overload
    def reducer(self, arg: Callable[[T, "Flux.Action"], Awaitable[T]]) -> Callable[[T, "Flux.Action"], Awaitable[T]]:
        ...

    @overload
    def reducer(self, arg: str) \
            -> Callable[[Callable[[T, "Flux.Action"], Awaitable[T]]], Callable[[T, "Flux.Action"], Awaitable[T]]]:
        ...

    def reducer(self, arg: Any) -> Any:
        if isinstance(arg, Callable):  # type: ignore
            return self.reducer(arg.__name__)(arg)  # type: ignore

        if not isinstance(arg, str):
            raise FluxError("reducer needs to be called with a name")

        t: Type = get_args(self.__orig_class__)[0] if hasattr(self, "__orig_class__") else None
        actyon: Actyon = self._get_or_create_actyon(arg, t)
        if len(actyon.producers) > 0:
            raise FluxError(f"reducer already exists: {arg}")

        async def state_consumer(state: List[t]) -> None:  # type: ignore
            if len(state) != 1:
                raise FluxError(f"invalid return value of reducer: {arg} ({len(state)} results)")
            self.state = state[0]

        def reducer_validator(sig: Signature) -> None:
            annotations: List[Type] = [p.annotation for p in sig.parameters.values()]
            if len(annotations) != 2 or t not in annotations or Flux.Action not in annotations:
                raise FluxError(f"invalid parameter annotation for reducer {arg}, needs: {t.__name__} and Flux.Action")

        actyon.consumer(state_consumer)
        return actyon.producer(validator=reducer_validator)

    def effect(self, name: str) -> Callable[[Callable[[T], Awaitable]], Callable[[T], Awaitable]]:
        # todo: verify async and signature
        t: Type = get_args(self.__orig_class__)[0] if hasattr(self, "__orig_class__") else None
        a: Actyon = self._get_or_create_actyon(name, t)

        def _effect_consumer(f: Callable[[t], Awaitable]) -> Callable[[t], Awaitable]:  # type: ignore
            async def _effect(state: List[t]) -> None:  # type: ignore
                await f(state[0])
            return a.consumer(_effect)  # type: ignore

        return _effect_consumer


class FluxHook(DisplayHook):
    @property
    def status(self) -> str:
        if self._running:
            return ""

        overall_state: ActyonState = self.overall_state or ActyonState.UNKNOWN
        status: str = get_symbol(overall_state)
        if self._color:
            status = overall_state.value + status + Style.RESET_ALL

        return status
