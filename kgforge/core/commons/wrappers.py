from typing import Any, Dict, List, Union

import hjson

from kgforge.core.commons.attributes import check_collisions, repr_
from kgforge.core.commons.typing import Hjson


class DictWrapper(dict):

    # TODO Should be immutable.

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def _wrap(data: Any) -> Any:
        if isinstance(data, Dict):
            return DictWrapper({k: DictWrapper._wrap(v) for k, v in data.items()})
        else:
            return data


class Filter:

    def __init__(self, path: List[str], operator: str, value: Any) -> None:
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

    @staticmethod
    def _wrap(template: Hjson) -> "PathsWrapper":
        def process(data: Any, path: List[str]) -> Union[PathsWrapper, PathWrapper]:
            if isinstance(data, Dict):
                return PathsWrapper(path, {k: process(v, path + [k]) for k, v in data.items()})
            else:
                return PathWrapper(path)
        loaded = hjson.loads(template)
        return process(loaded, [])
