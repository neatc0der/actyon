from re import sub
from typing import DefaultDict, Dict, List, Tuple

import attr

from actyon.helpers.log import get_logger


_log = get_logger()


def id_converter(identifier: str) -> str:
    new_id: str = sub("[^a-zA-Z0-9_]", "_", identifier.lower())
    if identifier != new_id:
        _log.warn(f'State ID was changed from ”{identifier}” to ”{new_id}”')

    return new_id


@attr.s
class State:
    initial: bool = attr.ib(default=False, kw_only=True)
    name: str = attr.ib()
    id: str = attr.ib(
        default=attr.Factory(lambda self: self.name.lower(), takes_self=True),
        converter=id_converter,
        kw_only=True,
    )
    transitions: Dict[str, "Transition"] = attr.ib(default=attr.Factory(dict), init=False)

    def to(self, to: "State", *triggers: str) -> "Transition":
        transition: Transition = Transition(source=self, target=to, triggers=triggers)
        for trigger in triggers:
            self.transitions[trigger] = transition
        return transition


@attr.s
class Transition:
    source: State = attr.ib()
    target: State = attr.ib()
    triggers: Tuple[str, ...] = attr.ib()
    after: Dict[str, List[str]] = attr.ib(default=attr.Factory(lambda: DefaultDict(list)), init=False)
