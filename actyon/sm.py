from inspect import getmembers
from logging import Logger
from typing import Any, Callable, Coroutine, DefaultDict, Dict, List, Tuple, Type

import attr
from colorama import Style

from .actyon import Actyon
from .console import DisplayHook, get_symbol
from .flux import Flux, FluxError
from .helpers.log import get_logger


_log: Logger = get_logger()


class StateError(FluxError):
    pass


@attr.s
class State:
    name: str = attr.ib()
    id: str = attr.ib(default=attr.Factory(lambda self: self.name.lower(), takes_self=True), kw_only=True)
    initial: bool = attr.ib(default=False, kw_only=True)

    transitions: Dict[str, "Transition"] = attr.ib(default=attr.Factory(dict), init=False)

    def to(self, to: "State", *triggers: Tuple[str]) -> "Transition":
        transition: Transition = Transition(source=self, target=to, triggers=triggers)
        for trigger in triggers:
            self.transitions[trigger] = transition
        return transition


@attr.s
class Transition:
    source: State = attr.ib()
    target: State = attr.ib()
    triggers: Tuple[str] = attr.ib()
    after: Dict[str, List[str]] = attr.ib(default=attr.Factory(lambda: DefaultDict(list)), init=False)


@attr.s
class StateStore:
    current: str = attr.ib()
    previous: str = attr.ib()
    states: Dict[str, State] = attr.ib()

    def shift(self, name: str) -> None:
        self.previous = self.current
        self.current = name

    @staticmethod
    def get_initial(states: Dict[str, State], t: Type) -> "StateStore":
        initial_states: List[State] = [s for s in states.values() if s.initial]
        if len(initial_states) == 0:
            raise StateError(f"no initial state defined for state machine: {t.__name__}")

        if len(initial_states) > 1:
            raise StateError(f"too many initial states defined for state machine: {t.__name__}")

        return StateStore(
            current=initial_states[0].id,
            previous=None,
            states=states,
        )


class StateMeta(type):
    def __new__(cls, name: str, bases: List[Type], dct: Dict[str, Any]) -> Type:
        dct["_transitions"] = DefaultDict(list)
        dct["_states"] = {}
        dct["_afters"] = []
        for key, after in dct.items():
            if key.startswith("after_") and isinstance(after, Callable):
                dct["_afters"].append(key)

        subcls = super().__new__(cls, name, bases, dct)
        subcls._states = {
            state.id: state
            for _, state in getmembers(subcls)
            if isinstance(state, State)
        }
        for state in subcls._states.values():
            for transition in state.transitions.values():
                for trigger in transition.triggers:
                    subcls._transitions[trigger].append(transition)

        return subcls


class StateMachine(metaclass=StateMeta):
    _transitions: Dict[str, List[Transition]]
    _states: Dict[str, State]
    _afters: List[str]

    def __init__(self, **options: Dict[str, Any]) -> None:
        self._flux: Flux[StateStore] = Flux[StateStore](
            initial=StateStore.get_initial(self._states, self.__class__),
            unsafe=True,
            **options,
        )
        self.initialize_flux()

        if isinstance(options.get("hook"), StateHook):
            options.get("hook").state_ref = self._flux.state

    def initialize_flux(self) -> None:
        for trigger in self._transitions.keys():
            self._flux.reducer(trigger)(self._reducer)

    @property
    def current(self) -> State:
        return self._flux.state.current

    async def _reducer(self, state: StateStore, action: Flux.Action) -> StateStore:
        transition: Transition = state.states[state.current].transitions.get(action.type)
        if transition is not None:
            state.shift(transition.target.id)
            after: str = f"after_{action.type}"
            if after in self._afters:
                await getattr(self, after)(state, action.data)

        return state

    async def run(self) -> None:
        await self._flux.run()

    async def done(self) -> None:
        await self._flux.done()

    async def trigger(self, name: str, **data: Dict[str, Any]) -> None:
        if Actyon.get(name) is None:
            _log.error(f"no trigger found: {name}")
        else:
            await self._flux.dispatch(name, **data)


class StateHook(DisplayHook):
    def __init__(self, color: bool = True) -> None:
        super().__init__(color)
        self._state_ref: StateStore = None
        self._str_len: int = 0

    @property
    def state_ref(self) -> StateStore:
        return self._state_ref

    @state_ref.setter
    def state_ref(self, state_ref: StateStore) -> None:
        self._state_ref = state_ref

    @property
    def status(self) -> str:
        if self._running:
            return ""

        status: str = get_symbol(self.overall_state)
        self._str_len = max(self._str_len, len(status) + len(self._message) + 1)
        whitespaces: int = self._str_len - len(status) - len(self._message) - 1
        status += " " * whitespaces + f" \u21E8 state: {self._state_ref.current}"

        if self._color:
            status = self.overall_state.value + status + Style.RESET_ALL

        return status
