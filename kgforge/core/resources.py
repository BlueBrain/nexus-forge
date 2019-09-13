from itertools import chain
from typing import Any, Dict, Iterator, List, Sequence, Union

from pandas import DataFrame


class Resource:

    def __init__(self, **properties) -> None:
        self.__dict__ = properties
        # Status of the last action performed on the resource.
        self._last_action = None
        # True if the resource is synchronized with the store.
        # False if the resource has not been registered yet or a modification has been done since
        # the synchronization.
        self._synchronized = False
        # True if the resource has been validated.
        # False if the entity has not been validated yet or a modification has been done since
        # the last validation.
        self._validated = False

    def __repr__(self) -> str:
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
                return "[" + ",".join(_repr(x, indent + 1) for x in data) + "],"
            else:
                return repr(data)
        return _repr(self, 0)

    def as_jsonld(self, compacted: bool = True) -> Dict:
        print("FIXME - Resource.as_jsonld()")
        return dict()


# FIXME Check if inheriting directly from 'list' is a good idea.
class Resources(list):

    def __init__(self, resources: Union[Sequence[Resource], Iterator[Resource]]) -> None:
        super().__init__(resources)

    def as_jsonld(self, compacted: bool = True) -> Dict:
        print("FIXME - Resources.as_jsonld()")
        return dict()

    def as_dataframe(self) -> DataFrame:
        print("FIXME - Resources.as_dataframe()")
        return DataFrame()
