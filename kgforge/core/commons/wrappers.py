from typing import Any, Dict, List

import hjson

from kgforge.core.commons.attributes import safe_setattr
from kgforge.core.commons.typing import Hjson


class DictWrapper(dict):

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
            return PathsWrapper({k: _wrap(v, path + [k]) for k, v in data.items()}, path=path)
        else:
            return PathWrapper(path)
    loaded = hjson.loads(template)
    return _wrap(loaded, [])


class Filter:

    def __init__(self, path: List[str], operator: str, value: Any):
        self.path = path
        self.operator = operator
        self.value = value


class FilterMixin:

    def __init__(self, path: List[str]) -> None:
        safe_setattr(self, "_path", path)

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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class PathsWrapper(FilterMixin):

    def __init__(self, paths: Dict, *args, **kwargs) -> None:
        self.__dict__ = paths
        super().__init__(*args, **kwargs)
