from itertools import chain
from typing import Any, List

from kgforge.core.commons.attributes import check_collisions


class Resource:

    # In the specializations:
    # POLICY Should declare added attributes names in a class attribute _RESERVED.
    # POLICY Should call attributes.check_collisions() with _RESERVED.

    _RESERVED = {"_last_action", "_validated", "_synchronized", "_store_metadata"}

    def __init__(self, **properties) -> None:
        check_collisions(self._RESERVED, properties.keys())
        self.__dict__ = properties
        # Status of the last modifying action performed on the resource.
        self._last_action = None
        # True if the resource has been validated.
        # False if the entity has not been validated yet or a modification has been done since
        # the last validation.
        self._validated = False
        # True if the resource is synchronized with the store.
        # False if the resource has not been registered yet or a modification has been done since
        # the synchronization.
        self._synchronized = False
        # None until synchronized.
        # Otherwise, holds metadata the potentially configured store returns at synchronization.
        self._store_metadata = None

    def __repr__(self) -> str:
        # FIXME Fusion with the Resources _repr() and simplify by moving to a sorting of __dict__.
        def _repr(data: Any, indent: int) -> str:
            if isinstance(data, Resource):
                top = ["type", "id"]
                space = " " * 3
                rind = f"\n{space * indent}"
                aind = f"{rind}{space}"
                first = [f"{x} = {getattr(data, x)}" for x in top if hasattr(data, x)]
                after = [f"{k} = {_repr(v, indent + 2)}" for k, v in data.__dict__.items()
                         if k not in top]
                return f"{rind}Resource({aind}{f',{aind}'.join(chain(first, after))})"
            elif isinstance(data, List):
                return f"[{','.join(_repr(x, indent + 1) for x in data)}],"
            else:
                return repr(data)
        return _repr(self, 0)

    def __setattr__(self, key, value) -> None:
        if key == "__dict__":
            self.__dict__.update(value)
        if key not in self._RESERVED:
            self.__dict__["_validated"] = False
            self.__dict__["_synchronized"] = False
        self.__dict__[key] = value


class Resources(list):

    def __init__(self, data, *args) -> None:
        resources = [data, *args] if args else data
        super().__init__(resources)

    def __repr__(self) -> str:
        # FIXME Fusion with the Resource _repr() and simplify by moving to a sorting of __dict__.
        def _repr(data: Any) -> str:
            top = ["type", "id"]
            if isinstance(data, Resource):
                first = [f"{x} = {getattr(data, x)}" for x in top if hasattr(data, x)]
                after = [f"{k} = {_repr(v)}" for k, v in data.__dict__.items() if k not in top]
                return f"Resource({','.join(chain(first, after))})"
            elif isinstance(data, List):
                short = [f"{p} = {getattr(r, p)}" for r in data[:3] for p in top if hasattr(r, p)]
                return f"[{', '.join(short)}]"
            else:
                return repr(data)
        sep = "\n,"
        return f"[{sep.join(_repr(x) for x in self)}\n]"
