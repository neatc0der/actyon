from asyncio import Queue, Task, create_task, gather
from copy import deepcopy
from inspect import Signature
from typing import Any, Callable, Dict, Generic, List, Tuple, Type, TypeVar, get_args, overload

import attr
from actyon import Actyon
from actyon.exceptions import ActyonError


class FluxError(ActyonError):
    pass


T = TypeVar("T")


class Flux(Generic[T]):
    @attr.s
    class Action:
        type: str = attr.ib()
        data: Dict[str, Any] = attr.ib(factory=dict)

    def __init__(self, initial: T):
        self._store: T = initial
        self._queue: Queue[Tuple[str, Dict[str, Any]]] = None
        self._task: Task = None

    @property
    def state(self) -> T:
        return deepcopy(self._store)

    @state.setter
    def state(self, state: T) -> None:
        self._store = state

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

            actyon: Actyon = Actyon.get(name)
            if actyon is None:
                raise FluxError(f"unknown action: {name}")

            if not isinstance(data, Flux.Action):
                data = Flux.Action(type=name, data=data)

            await actyon.execute(self.state, data)

            self._queue.task_done()

    async def done(self) -> None:
        if self._task is None:
            raise FluxError("flux is not running")

        await self._queue.join()
        if not self._task.done:
            self._task.cancel()
            await gather(self._task, return_exceptions=True)

        self._task = None

    async def dispatch(self, name: str, **data: Dict[str, Any]) -> None:
        await self._queue.put((name, data))

    @overload
    def reducer(self, arg: Callable[[T, "Flux.Action"], T]) -> Callable[[T, "Flux.Action"], T]: ...

    @overload
    def reducer(self, arg: str) -> Callable[[Callable[[T, "Flux.Action"], T]], Callable[[T, "Flux.Action"], T]]: ...

    def reducer(self, arg: Any) -> Any:
        if isinstance(arg, Callable):
            return self.reducer(arg.__name__)(arg)

        if not isinstance(arg, str):
            raise FluxError("reducer needs to be called with a name")

        t: Type = get_args(self.__orig_class__)[0] if hasattr(self, "__orig_class__") else None
        actyon: Actyon = Actyon.get_or_create(arg, t)
        if len(actyon.producers) > 0:
            raise FluxError(f"reducer already exists: {arg}")

        async def state_consumer(state: List[t]) -> None:
            if len(state) != 1:
                raise FluxError(f"invalid return value of reducer: {arg} ({len(state)} results)")
            self.state = state[0]

        def reducer_validator(sig: Signature) -> None:
            annotations: List[Type] = [p.annotation for p in sig.parameters.values()]
            if len(annotations) != 2 or t not in annotations or Flux.Action not in annotations:
                raise FluxError(f"invalid parameter annotation for reducer {arg}, needs: {t.__name__} and Flux.Action")

        actyon.consumer(state_consumer)
        return actyon.producer(validator=reducer_validator)

    def effect(self, name: str) -> Callable[[Callable[[T], None]], Callable[[T], None]]:
        t: Type = get_args(self.__orig_class__)[0] if hasattr(self, "__orig_class__") else None
        actyon: Actyon = Actyon.get_or_create(name, t)

        def _effect_consumer(f: Callable[[t], None]) -> Callable[[t], None]:
            async def effect(state: List[t]) -> None:
                await f(state[0])
            return actyon.consumer(effect)

        return _effect_consumer
