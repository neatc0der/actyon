from inspect import Signature, signature
from itertools import product
from typing import Any, Callable, Dict, Iterable, Iterator, List, Tuple, Type


class Injector:
    def __init__(self, obj: Any) -> None:
        self._obj: Any = obj
        self._dependencies: Dict[Type, List[Any]] = self._unpack(obj)

    def _unpack(self, obj: Any) -> Dict[Type, List[Any]]:
        if type(obj).__module__ in ("typing", "builtins") and (isinstance(obj, (str, bytes, bytearray)) or
                                                               not isinstance(obj, Iterable)):
            return {}

        instances: Dict[Type, List[Any]] = {
            type(obj): [obj],
        }

        subobjects: Iterable = ()
        if isinstance(obj, Iterable):
            subobjects = obj
        elif hasattr(obj, '__dict__'):
            subobjects = obj.__dict__.values()
        elif hasattr(obj, '__slots__'):
            subobjects = (getattr(obj, a) for a in obj.__slots__)

        for o in subobjects:
            if o not in instances.get(type(o), []):
                for key, value in self._unpack(o).items():
                    instances[key] = instances.get(key, []) + value

        return instances

    def add(self, obj: Any, t: Type = None) -> None:
        key: Type = t or type(obj)
        self._dependencies[key] = self._dependencies.get(key, []) + [obj]

    def inject_to(self, func: Callable[..., Any]) -> Iterator[Any]:
        sig: Signature = signature(func)
        keywords: List[str] = [name for name in sig.parameters.keys()]

        combinations: Iterator[Tuple[Any, ...]] = product(*(
            self._dependencies.get(p.annotation, [])
            for p in sig.parameters.values()
        ))

        for values in combinations:
            yield func(**dict(zip(keywords, values)))
