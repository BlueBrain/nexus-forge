# 
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.

from typing import Any, Dict, List, Union

from kgforge.core.commons.attributes import check_collisions, repr_class


class Filter:

    def __init__(self, path: List[str], operator: str, value: Any) -> None:
        self.path: List[str] = path
        self.operator: str = operator
        self.value: Any = value

    def __repr__(self) -> str:
        return repr_class(self)


class FilterMixin:

    _RESERVED = {"_path"}

    def __init__(self, path: List[str]) -> None:
        self._path: List[str] = path

    def __repr__(self) -> str:
        return repr_class(self)

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


def wrap_paths(template: Dict) -> PathsWrapper:
    return _wrap(template, [])


def _wrap(data: Any, path: List[str]) -> Union[PathsWrapper, PathWrapper]:
    if isinstance(data, Dict):
        return PathsWrapper(path, {k: _wrap(v, path + [k]) for k, v in data.items()})
    else:
        return PathWrapper(path)
