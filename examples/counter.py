from asyncio import run

from actyon.flux import Flux
import attr


@attr.s
class Counter:
    value: int = attr.ib()


flux: Flux = Flux[Counter](
    initial=Counter(0),
)


@flux.reducer
async def increment(state: Counter, action: Flux.Action) -> Counter:
    state.value += action.data.get("inc", 1)
    print(state)
    return state


@flux.effect("increment")
async def increment_effect(state: Counter) -> None:
    if state.value < 10:
        await flux.dispatch("increment", inc=state.value)


async def main() -> None:
    await flux.run()
    await flux.dispatch("increment")
    await flux.done()


if __name__ == "__main__":
    run(main())
