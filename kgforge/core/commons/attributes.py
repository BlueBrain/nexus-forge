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

from typing import KeysView, Set, Tuple


def check_collisions(reserved: Set[str], new: KeysView[str]) -> None:
    intersect = reserved.intersection(set(new))
    if intersect:
        raise NotImplementedError(f"some names of the given properties are reserved: {intersect}")


def sort_attrs(kv: Tuple[str, str]) -> Tuple[int, str]:
    # POLICY Should be called to sort attributes of resources, templates, mappings, ...
    ordered = ["_last_action", "_validated", "_synchronized", "_store_metadata",
               "context", "id", "type", "label"]
    orders = {x: i for i, x in enumerate(ordered)}
    next_order = len(ordered) + 1
    return orders.get(kv[0], next_order), kv[0]


def repr_class(self: object) -> str:
    ordered = sorted(self.__dict__.items(), key=sort_attrs)
    attributes = (f"{k}={v!r}" for k, v in ordered)
    attributes_str = ", ".join(attributes)
    class_name = type(self).__name__
    return f"{class_name}({attributes_str})"


def eq_class(self: object, other: object) -> bool:
    return self.__dict__ == other.__dict__ if type(other) is type(self) else False
