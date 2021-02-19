from collections import defaultdict
from inspect import Signature, signature
from itertools import product
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Iterable, Iterator, List, Tuple, Type

from .log import get_logger


log: Logger = get_logger()


class Injector:
    def __init__(self, obj: Any) -> None:
        self._obj: Any = obj
        self._dependencies: Dict[Type, List[Any]] = self._unpack(obj)

    def _unpack(self, obj: Any) -> Dict[Type, List[Any]]:
        instances: Dict[Type, List[Any]] = defaultdict(lambda: [])
        open_objs: List[Any] = [obj]
        count: int = 0
        while len(open_objs) > 0:
            if count > 999:
                log.error(f"injector crawled in deep data structure - aborting after {count} iterations")
                break
            count += 1
            for i in range(len(open_objs)):
                sub_obj: Any = open_objs.pop()
                sub_type: Type = type(sub_obj)
                if sub_obj is None or sub_type in (str, bytes, bytearray, type):
                    continue
                if isinstance(sub_obj, Iterable) or sub_obj not in instances[sub_type]:
                    if sub_type.__module__ not in ("typing", "builtins"):
                        instances[sub_type].append(sub_obj)

                    if isinstance(sub_obj, Dict):
                        open_objs.extend(list(sub_obj.values()))
                    elif isinstance(sub_obj, Iterable):
                        open_objs.extend(list(sub_obj))
                    elif hasattr(obj, '__slots__'):
                        open_objs.extend([getattr(obj, a) for a in obj.__slots__])
                    elif hasattr(obj, '__dict__'):
                        open_objs.extend(list(obj.__dict__.values()))

        return dict(instances)

    def add(self, obj: Any, t: Type = None.__class__) -> None:
        key: Type = t or type(obj)
        self._dependencies[key] = self._dependencies.get(key, []) + [obj]

    def inject_to(self, func: Callable[..., Awaitable]) -> Iterator[Any]:
        sig: Signature = signature(func)
        keywords: List[str] = [name for name in sig.parameters.keys()]

        combinations: Iterator[Tuple[Any, ...]] = product(*(
            self._dependencies.get(p.annotation, [])
            for p in sig.parameters.values()
        ))

        async def _wrapper(**kwargs: Any) -> List[Any]:
            return [await func(**kwargs)]

        f: Callable[..., Awaitable] = _wrapper if not issubclass(sig.return_annotation, List) else func  # type: ignore

        for values in combinations:
            yield f(**dict(zip(keywords, values)))
