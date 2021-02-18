from inspect import getmembers
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Tuple, Type

from actyon.flux import FluxError
import attr

from .state import State, Transition


class StateError(FluxError):
    pass


@attr.s
class StateStore:
    current: str = attr.ib()
    previous: Optional[str] = attr.ib()
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


class BaseStateMachine:
    _transitions: Dict[str, List[Transition]]
    _states: Dict[str, State]
    _afters: List[str]


class StateMeta(type):
    def __new__(cls, name: str, bases: Tuple[Type, ...], dct: Dict[str, Any]) -> type:  # type: ignore
        dct["_transitions"] = DefaultDict(list)
        dct["_states"] = {}
        dct["_afters"] = []
        for key, after in dct.items():
            if key.startswith("after_") and isinstance(after, Callable):  # type: ignore
                dct["_afters"].append(key)

        subcls: Type[BaseStateMachine] = super().__new__(cls, name, bases, dct)
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
