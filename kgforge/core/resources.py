from itertools import chain
from typing import Any, Iterator, List, Sequence, Union

from kgforge.core.commons.attributes import safe_setattr


class Resource:

    def __init__(self, **properties) -> None:
        self.__dict__ = properties
        # Status of the last modifying action performed on the resource.
        safe_setattr(self, "_last_action", None)
        # True if the resource has been validated.
        # False if the entity has not been validated yet or a modification has been done since
        # the last validation.
        safe_setattr(self, "_validated", False)
        # True if the resource is synchronized with the store.
        # False if the resource has not been registered yet or a modification has been done since
        # the synchronization.
        safe_setattr(self, "_synchronized", False)
        # None until synchronized.
        # Otherwise, holds metadata the potentially configured store returns at synchronization.
        safe_setattr(self, "_store_metadata", None)

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
        self._validated = False
        self._synchronized = False
        # Should be last to not override operations modifying the previous attributes.
        safe_setattr(self, key, value)


class Resources(list):

    def __init__(self, resources: Union[Sequence[Resource], Iterator[Resource]]) -> None:
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
