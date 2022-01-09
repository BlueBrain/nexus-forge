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
from enum import Enum, auto

from typing import Any, Dict, List, Union

from kgforge.core.commons.attributes import check_collisions, repr_class


class FilterOperator(Enum):
    EQUAL = "__eq__"
    NOT_EQUAL = "__ne__"
    LOWER_THAN = "__lt__"
    LOWER_OR_Equal_Than = "__le__"
    GREATER_Than = "__gt__"
    GREATER_OR_Equal_Than = "__ge__"


class Filter:
    def __init__(self, path: List[str], operator: str, value: Any) -> None:
        self.path: List[str] = path
        try:
            self.operator: str = FilterOperator(operator).value
        except Exception as e:
            raise ValueError(
                f"Invalid operator value '{operator}'. Allowed operators are {[member.value for name, member in FilterOperator.__members__.items()]}"
            )
        self.value: Any = value

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.path == other.path
            and self.operator == other.operator
            and self.value == other.value
        )

    def __repr__(self) -> str:
        return repr_class(self)


class FilterMixin:

    _RESERVED = {"_path"}

    def __init__(self, path: List[str]) -> None:
        self._path: List[str] = path

    def __repr__(self) -> str:
        return repr_class(self)

    def __lt__(self, other: Any) -> Filter:
        return self._for(FilterOperator.LOWER_THAN.value, other)

    def __le__(self, other: Any) -> Filter:
        return self._for(FilterOperator.LOWER_OR_Equal_Than.value, other)

    def __eq__(self, other: Any) -> Filter:
        return self._for(FilterOperator.EQUAL.value, other)

    def __ne__(self, other: Any) -> Filter:
        return self._for(FilterOperator.NOT_EQUAL.value, other)

    def __gt__(self, other: Any) -> Filter:
        return self._for(FilterOperator.GREATER_Than.value, other)

    def __ge__(self, other: Any) -> Filter:
        return self._for(FilterOperator.GREATER_OR_Equal_Than.value, other)

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


def create_filters_from_dict(filter_dict: Dict, path_prefix=None) -> List[Filter]:
    filters = list()
    if path_prefix is None:
        path_prefix = []
    for k, v in filter_dict.items():
        path_prefix.append(k)
        path = list(path_prefix)
        if isinstance(v, dict):
            filters.extend(create_filters_from_dict(v, path))
        else:
            filters.append(Filter(path, FilterOperator.EQUAL.value, v))
        path_prefix.remove(k)
    return filters
