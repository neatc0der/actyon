from asyncio.tasks import Task, create_task, sleep
from enum import Enum
from sys import stdout
from typing import Dict, List, Optional

from colorama import Fore, Style
from progress.spinner import PixelSpinner

from .actyon import Actyon
from .helpers.log import get_logger
from .hook import ActyonHook, HookEvent, HookEventType


log = get_logger()


class ActyonState(Enum):
    ERROR = Fore.RED
    WARN = Fore.YELLOW
    OKAY = Fore.GREEN
    UNKNOWN = Style.NORMAL


class ActyonPhase(Enum):
    PRODUCE = "\u25B6"  # arrow right
    CONSUME = "\u25C0"  # arrow left


def get_symbol(state: ActyonState) -> str:
    if state == ActyonState.OKAY:
        return "\u2713"  # tick
    elif state == ActyonState.WARN:
        return "\u26A0"  # warning sign
    elif state == ActyonState.ERROR:
        return "\u2717"  # cross

    return "\u25CF"  # circle


class HookPixelSpinner(PixelSpinner):
    phases = [c + Style.RESET_ALL + "\r" for c in PixelSpinner.phases]


class DisplayHook(ActyonHook):
    def __init__(self, color: bool = True) -> None:
        self._color = color
        self._future: Optional[Task] = None
        self._running: bool = False
        self._phase: ActyonPhase = ActyonPhase.PRODUCE
        self._state: Dict[ActyonPhase, ActyonState] = {
            phase: ActyonState.UNKNOWN
            for phase in ActyonPhase
        }
        self._message: str = ""

    @property
    def state(self) -> ActyonState:
        return self._state[self._phase]

    @state.setter
    def state(self, state: ActyonState) -> None:
        self._state[self._phase] = state

    @property
    def overall_state(self) -> Optional[ActyonState]:
        for state in ActyonState:
            if state in self._state.values():
                return state

        return None

    @property
    def phase(self) -> ActyonPhase:
        return self._phase

    @phase.setter
    def phase(self, phase: ActyonPhase) -> None:
        self._phase = phase

    async def event(self, event: HookEvent) -> None:
        if event.type == HookEventType.START:
            log.info(f"actyon stared: {event.action.name}")
            self.phase = ActyonPhase.PRODUCE
            self.state = ActyonState.UNKNOWN
            self._running = True
            self._future = create_task(self._spin(event.action))

        elif event.type == HookEventType.AFTER_PRODUCE:
            self.phase = ActyonPhase.CONSUME

        elif event.type == HookEventType.PRELIMINARY_EMPTY:
            if self.state not in (ActyonState.OKAY, ActyonState.ERROR):
                self.state = ActyonState.WARN

        elif event.type in (HookEventType.NO_CONSUMER, HookEventType.NO_PRODUCER):
            if self.state != ActyonState.ERROR:
                self.state = ActyonState.WARN

        elif event.type == HookEventType.RESULT_PRODUCED:
            if self.state != ActyonState.ERROR:
                self.state = ActyonState.OKAY

        elif event.type == HookEventType.FAIL:
            self.state = ActyonState.ERROR

        elif event.type == HookEventType.END:
            if self.state == ActyonState.UNKNOWN:
                self.state = ActyonState.OKAY
            self._running = False
            if self._future is not None and not self._future.done():
                await self._future
            log.info(f"actyon ended: {event.action.name}")

    @property
    def status(self) -> str:
        status: List[str] = []
        for phase in ActyonPhase:  # type: ignore
            if phase == self._phase and self._running:
                break

            if self._color:
                status.append(self._state[phase].value + phase.value + Style.RESET_ALL)
            else:
                status.append(phase.value + get_symbol(self._state[phase]))

        return " ".join(status)

    async def _spin(self, actyon: Actyon) -> None:
        prefix: str = self.state.value if self._color else ""
        self._message = f"Actyon: {actyon.name} "
        spinner: PixelSpinner = HookPixelSpinner(prefix + self._message, file=stdout)
        try:
            while self._running:
                await sleep(0.1)
                prefix = self.overall_state.value if self._color and self.overall_state is not None else ""
                spinner.message = f"{prefix}{self._message}{self.status}".strip() + " "
                spinner.next()

        finally:
            spinner.write("")
            spinner.finish()
