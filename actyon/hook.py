from enum import Enum

import actyon
import attr


class HookEventType(Enum):
    START = "start"
    AFTER_PRODUCE = "after_produce"
    PRELIMINARY_EMPTY = "preliminary_empty"
    RESULT_PRODUCED = "result_produced"
    NO_CONSUMER = "no_consumer"
    NO_PRODUCER = "no_producer"
    FAIL = "fail"
    END = "end"


@attr.s
class HookEvent:
    type: HookEventType = attr.ib()
    action: "actyon.Actyon" = attr.ib()


class ActyonHook:
    async def event(self, event: HookEvent) -> None:
        raise NotImplementedError()
