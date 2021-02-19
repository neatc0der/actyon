from asyncio import run, sleep
from time import time
from typing import Any, Dict

from actyon.sm import State, StateMachine, StateStore
from colorama import Back, Fore, Style


class TrafficLight(StateMachine):
    red: State = State("Red", initial=True)
    yellow: State = State("Yellow")
    green: State = State("Green")

    red.to(yellow, "go")
    yellow.to(green, "go")
    yellow.to(red, "stop")
    green.to(yellow, "stop")

    def __init__(self, **options: Dict[str, Any]) -> None:
        super().__init__(**options)
        self._start: float = time()

    async def after_go(self, state: StateStore, data: Dict[str, Any]) -> None:
        self.print(state.current)
        if state.current == "yellow":
            await sleep(1.0)
            await self.trigger("go")

        elif state.current == "green":
            await sleep(5.0)
            await self.trigger("stop")

    async def after_stop(self, state: StateStore, data: Dict[str, Any]) -> None:
        self.print(state.current)
        if state.current == "yellow":
            await sleep(1.0)
            await self.trigger("stop")

    def print(self, value: str, header: bool = False) -> None:
        light: Dict[str, str] = {
            "red": Fore.RED + "\u25CF",
            "yellow": Fore.YELLOW + "\u25CF",
            "green": Fore.GREEN + "\u25CF",
            "off": Fore.WHITE + "\u25CB",
        }
        t: float = time() - self._start
        self._start = time()

        if header:
            print("RYG")

        print(
            Back.BLACK + "".join([
                light[key if key == value else "off"]
                for key in ("red", "yellow", "green")
            ]) + Style.RESET_ALL,
            f"runtime: {t:.4f} seconds",
        )


async def main() -> None:
    traffic_light: TrafficLight = TrafficLight()
    traffic_light.print(traffic_light.current, header=True)
    await traffic_light.run()
    await traffic_light.trigger("go")
    await traffic_light.done()


if __name__ == "__main__":
    run(main())
