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
from typing import Any, Dict, Optional, Union, List, Tuple

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
    _RESERVED = {"_last_action", "_validated", "_synchronized", "_store_metadata", "_forge", "_inner_sync"}

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
        self._inner_sync: bool = False
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
        elif key == "_synchronized":
            self._set_synchronized(value)
        self.__dict__[key] = value

    @staticmethod
    def _sync_resource(item, vlist, sync_value=True):
        if isinstance(item, Resource):
            if sync_value:
                vlist.append(item._synchronized)
            else:
                vlist.append(item)

    def _get_synchronized(self) -> bool:
        inner = []
        for v in self.__dict__.values():
            if isinstance(v, List):
                for iv in v:
                    self._sync_resource(iv, inner)
            else:
                self._sync_resource(v, inner)
        if inner:
            self._inner_sync = (all(inner))
        if self._inner_sync is False:    
            return False
        else:
            return self.__dict__["_synchronized"]
    
    def _set_synchronized(self, sync: bool) -> None:
        inner = []
        for v in self.__dict__.values():
            if isinstance(v, List):
                for iv in v:
                    self._sync_resource(iv, inner, sync_value=False)
            else:
                self._sync_resource(v, inner, sync_value=False)
        if inner:
            for iresource in inner:
                iresource._synchronized = sync
        self.__dict__["_inner_sync"] = sync
    
    _synchronized = property(_get_synchronized, _set_synchronized)

    def has_identifier(self, return_attribute: bool = False) ->  Union[bool, Tuple[bool, str]]:
        res = self._has_term("id", return_attribute)
        return res

    def has_type(self, return_attribute: bool = False) -> Union[bool, Tuple[bool, str]]:
        return self._has_term("type", return_attribute)
    
    def _has_term(self, term, return_attribute):
        result = False
        attribute = None
        if hasattr(self, f"@{term}"):
            result= True
            attribute = f"@{term}"
        if hasattr(self, term):
            result= True
            attribute = term
        if return_attribute:
            return (result, attribute)
        else:
            return result

    def get_type(self) -> Union[str, List[str]]:
        resource_has_type, type_key = self.has_type(return_attribute=True)
        return getattr(self, type_key) if resource_has_type else None

    def get_identifier(self) -> str:
        resource_has_id, id_key = self.has_identifier(return_attribute=True)
        return getattr(self, id_key) if resource_has_id else None

    @classmethod
    def from_json(cls, data: Union[Dict, List[Dict]], na: Union[Any, List[Any]] = None):

        def _(d: Union[Dict, List[Dict]], nas: List[Any]) -> Resource:
            if isinstance(d, List):
                return [_(x,  nas) for x in d]
            elif isinstance(d, Dict):
                properties = {k: _(v, nas) for k, v in d.items() if v not in nas}
                return Resource(**properties)
            else:
                return d

        nas = na if isinstance(na, List) else [na]
        return [_(d, nas) for d in data] if isinstance(data, List) else _(data, nas)


def encode(data: Any) -> Union[str, Dict]:
    if isinstance(data, Resource):
        return {k: v for k, v in data.__dict__.items() if k not in data._RESERVED}
    elif type(data).__name__ == "LazyAction":
        return str(data)
    elif isinstance(data, set) or isinstance(data, list):
        return {encode(r) for r in data}
    else:
        return data.__dict__
