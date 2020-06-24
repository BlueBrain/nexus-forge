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

from typing import Any, Dict, Optional, Union

import hjson

from kgforge.core.commons.attributes import check_collisions, repr_class, sort_attrs
from kgforge.core.wrappings.dict import DictWrapper


# NB: Do not 'from kgforge.core.commons.actions import Action' to avoid cyclic dependency.


class Resource:

    # See datasets.py in kgforge/specializations/resources/ for a reference specialization.

    # POLICY Specializations could add methods and attributes if they are added to _RESERVED.
    # TODO Move from BDD to classical testing to have a more parameterizable test suite. DKE-135.
    # POLICY Specializations should pass tests/core/resources/resource.feature tests.

    # FIXME remove "_forge" from _RESERVED and implement a "cast" of derived classes to Resource
    _RESERVED = {"_last_action", "_validated", "_synchronized", "_store_metadata", "_forge"}

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
        self._store_metadata: Optional[DictWrapper] = None

    def __repr__(self) -> str:
        return repr_class(self)

    def __str__(self) -> str:
        return hjson.dumps(self, indent=4, default=encode, item_sort_key=sort_attrs)

    def __eq__(self, other: object) -> bool:
        def _data(resource: Resource) -> Dict:
            return {k: _data(v) if isinstance(v, Resource) else v
                    for k, v in resource.__dict__.items()
                    if k not in resource._RESERVED}
        if type(other) is type(self):
            sdict = _data(self)
            odict = _data(other)
            return sdict == odict
        else:
            return False

    def __setattr__(self, key, value) -> None:
        if key not in self._RESERVED:
            self.__dict__["_validated"] = False
            self.__dict__["_synchronized"] = False
        self.__dict__[key] = value


def encode(data: Any) -> Union[str, Dict]:
    if isinstance(data, Resource):
        return {k: v for k, v in data.__dict__.items() if k not in data._RESERVED}
    elif type(data).__name__ == "LazyAction":
        return str(data)
    else:
        return data.__dict__
