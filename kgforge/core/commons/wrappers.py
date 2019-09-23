from typing import Any, Dict, List

import hjson

from kgforge.core.commons.attributes import check_collisions, repr_
from kgforge.core.commons.typing import Hjson


class DictWrapper(dict):

    # TODO Should be immutable.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def wrap(data: Any):
        if isinstance(data, Dict):
            return DictWrapper({k: DictWrapper.wrap(v) for k, v in data.items()})
        else:
            return data


def wrap_paths(template: Hjson) -> "PathsWrapper":
    def _wrap(data: Any, path: List[str]):
        if isinstance(data, Dict):
            return PathsWrapper(path, {k: _wrap(v, path + [k]) for k, v in data.items()})
        else:
            return PathWrapper(path)
    loaded = hjson.loads(template)
    return _wrap(loaded, [])


class Filter:

    def __init__(self, path: List[str], operator: str, value: Any):
        self.path = path
        self.operator = operator
        self.value = value

    def __repr__(self) -> str:
        return repr_(self)


class FilterMixin:

    _RESERVED = {"_path"}

    def __init__(self, path: List[str]) -> None:
        self._path = path

    def __lt__(self, other: Any) -> Filter:
        return self._for("__lt__", other)

    def __le__(self, other: Any) -> Filter:
        return self._for("__le__", other)

    def __eq__(self, other: Any) -> Filter:
        return self._for("__eq__", other)

    def __ne__(self, other: Any) -> Filter:
        return self._for("__ne__", other)

    def __gt__(self, other: Any) -> Filter:
        return self._for("__gt__", other)

    def __ge__(self, other: Any) -> Filter:
        return self._for("__ge__", other)

    def _for(self, operator: str, other: Any) -> Filter:
        return Filter(self._path, operator, other)


class PathWrapper(FilterMixin):

    def __init__(self, path: List[str]) -> None:
        super().__init__(path)


class PathsWrapper(FilterMixin):

    def __init__(self, path: List[str], paths: Dict) -> None:
        check_collisions(self._RESERVED, paths.keys())
        super().__init__(path)
        self.__dict__ = paths
