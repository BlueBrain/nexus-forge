# 
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

from typing import Any, Dict, Iterable, Optional, Union

import hjson

from kgforge.core.commons.attributes import check_collisions, sort_attributes


class Resource:

    # Specializations:
    # POLICY Should add new attributes to _RESERVED.
    # See datasets.py in kgforge/specializations/resources for a specialization.
    # Specializations should pass tests/core/resources/resource.feature tests.

    _RESERVED = {"_last_action", "_validated", "_synchronized", "_store_metadata", "_context"}

    def __init__(self, **properties) -> None:
        check_collisions(self._RESERVED, properties.keys())
        self.__dict__.update(properties)
        # Status of the last modifying action performed on the resource.
        self._last_action: Optional["Action"] = None
        # True if the resource has been validated.
        # False if the resource has not been validated yet or a modification has been done since
        # the last validation.
        self._validated: bool = False
        # True if the resource is synchronized with the store.
        # False if the resource has not been registered yet or a modification has been done since
        # the synchronization.
        self._synchronized: bool = False
        # None until synchronized.
        # Otherwise, holds the metadata the store returns at synchronization.
        self._store_metadata: Optional["DictWrapper"] = None

    def __repr__(self) -> str:
        ordered = sorted(self.__dict__.items(), key=sort_attributes)
        attributes = (f"{k}={repr(v)}" for k, v in ordered)
        attributes_str = ', '.join(attributes)
        return f"Resource({attributes_str})"

    def __str__(self) -> str:
        return hjson.dumps(self, indent=4, default=_encode, item_sort_key=sort_attributes)

    def __setattr__(self, key, value) -> None:
        if key not in self._RESERVED:
            self.__dict__["_validated"] = False
            self.__dict__["_synchronized"] = False
        self.__dict__[key] = value


class Resources(list):

    def __init__(self, data: Union[Resource, Iterable[Resource]], *resources) -> None:
        resources = [data, *resources] if resources else data
        super().__init__(resources)

    def __str__(self) -> str:
        return hjson.dumps(self, indent=4, default=_encode)


def _encode(data: Any) -> Union[str, Dict]:
    if isinstance(data, Resource):
        return {k: v for k, v in data.__dict__.items() if k not in data._RESERVED}
    elif type(data).__name__ == "LazyAction":
        return str(data)
    else:
        return data.__dict__
