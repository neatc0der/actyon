from logging import Logger
from typing import Any, Optional, cast

from actyon.console import ActyonState, DisplayHook, get_symbol
from actyon.flux import Flux
from actyon.helpers.log import get_logger
from colorama import Style

from .base import BaseStateMachine, StateMeta, StateStore
from .state import Transition


_log: Logger = get_logger()


class StateMachine(BaseStateMachine, metaclass=StateMeta):
    def __init__(self, **options: Any) -> None:
        self._flux: Flux[StateStore] = Flux[StateStore](
            initial=StateStore.get_initial(self._states, self.__class__),
            unsafe=True,
            **options,
        )
        self.initialize_flux()

        if isinstance(options.get("hook"), StateHook):
            cast(StateHook, options.get("hook")).store_ref = self._flux.state

    def initialize_flux(self) -> None:
        for trigger in self._transitions.keys():
            self._flux.reducer(trigger)(self._reducer)

    @property
    def current(self) -> str:
        return self._flux.state.current

    async def _reducer(self, state: StateStore, action: Flux.Action) -> StateStore:
        transition: Optional[Transition] = state.states[state.current].transitions.get(action.type)
        if transition is not None:
            state.shift(transition.target.id)
            after: str = f"after_{action.type}"
            if after in self._afters:
                await getattr(self, after)(state, action.data)
        else:
            _log.info(f'state "{state.current}" has no transition for trigger: {action.type}')

        return state

    async def run(self) -> None:
        await self._flux.run()

    async def done(self) -> None:
        await self._flux.done()

    async def trigger(self, name: str, **data: Any) -> None:
        if self._flux.actyons.get(name) is None:
            _log.error(f"no trigger found: {name}")
        else:
            await self._flux.dispatch(name, **data)


class StateHook(DisplayHook):
    def __init__(self, color: bool = True) -> None:
        super().__init__(color)
        self._state_ref: Optional[StateStore] = None
        self._str_len: int = 0

    @property
    def store_ref(self) -> Optional[StateStore]:
        return self._state_ref

    @store_ref.setter
    def store_ref(self, state_ref: StateStore) -> None:
        self._state_ref = state_ref

    @property
    def status(self) -> str:
        if self._running:
            return ""

        overall_state: ActyonState = self.overall_state or ActyonState.UNKNOWN
        status: str = get_symbol(overall_state)
        self._str_len = max(self._str_len, len(status) + len(self._message) + 1)
        whitespaces: int = self._str_len - len(status) - len(self._message) - 1
        current: str = self._state_ref.current if self._state_ref is not None else "none"
        status += " " * whitespaces + f" \u21E8 state: {current}"

        if self._color:
            status = overall_state.value + status + Style.RESET_ALL

        return status
