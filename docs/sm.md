# State Machine

## Usage

Define your `State`s and `Transition`s in your very own `StateMachine`:

```python
from actyon.sm import State, StateMachine, StateStore

class MyMachine(StateMachine):
    state_1: State = State("state_1")
    state_2: State = State("state_2")

    state_1.to(state_2, "my_transition")
```

Afterwards you may want to add logic to your state changes. Feel free:

```python
my_machine: MyMachine = MyMachine()

@my_machine.after("my_transition")
async def after_my_transition(state: StateStore, data: Dict[str, Any]) -> None:
    print(state.previous, "->", state.current)
    print("bomb went off:", data.get("tick_tick", "puff"))
```

Finally, run your machine:

```python
    await traffic_light.run()
    await traffic_light.trigger("my_transition", tick_tick="boom")
    await traffic_light.done()
```

## Example: Traffic Light

Please find the code [here](https://github.com/neatc0der/actyon/tree/master/examples/traffic_light.py).

```mermaid
stateDiagram-v2
    [*] --> Red: run()
    Red --> [*]: done()
    Red --> Yellow: go
    Yellow --> Green: go
    Green --> Yellow: stop
    Yellow --> Red: stop
```

## Experimental

Registering a hook introduces a neat debug output on transitions:

```python
from actyon.sm import StateHook

my_machine: MyMachine = MyMachine(hook=StateHook())
```

Result:

```shell
$ python my_machine.py
Actyon: my_transition ✓ ⇨ state: state_2
```
