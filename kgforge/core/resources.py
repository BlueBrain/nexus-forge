from typing import Dict, Optional

import hjson

from kgforge.core.commons.attributes import check_collisions, sort_attributes


class Resource:

    # Specializations:
    # POLICY Should declare added attributes in _RESERVED while keeping the ones from the specialized class.
    # POLICY Should call attributes.check_collisions() with _RESERVED before super().__init__().
    # See datasets.py in kgforge/specializations/resources for a specialization.
    # Specializations should pass tests/core/resources/resource.feature tests.

    _RESERVED = {"_last_action", "_validated", "_synchronized", "_store_metadata"}

    def __init__(self, **properties) -> None:
        check_collisions(self._RESERVED, properties.keys())
        self.__dict__.update(properties)
        # Status of the last modifying action performed on the resource.
        self._last_action: "Optional[Action]" = None
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
        self._store_metadata: "Optional[DictWrapper]" = None

    def __repr__(self) -> str:
        ordered = sorted(self.__dict__.items(), key=sort_attributes)
        attributes = (f"{k}={repr(v)}" for k, v in ordered)
        attributes_str = ', '.join(attributes)
        return f"Resource({attributes_str})"

    def __str__(self) -> str:
        return _str(self)

    def __setattr__(self, key, value) -> None:
        if key not in self._RESERVED:
            self.__dict__["_validated"] = False
            self.__dict__["_synchronized"] = False
        self.__dict__[key] = value


class Resources(list):

    def __init__(self, data, *args) -> None:
        resources = [data, *args] if args else data
        super().__init__(resources)

    def __str__(self) -> str:
        return _str(self)


def _str(data: "ManagedData") -> str:
    def _as_dict(x) -> Dict:
        return {k: v for k, v in x.__dict__.items() if k not in Resource._RESERVED}
    return hjson.dumps(data, indent=4, default=_as_dict, item_sort_key=sort_attributes)
