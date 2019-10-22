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

import inspect
from typing import Any, KeysView, Optional, Set, Tuple


def check_collisions(reserved: Set[str], new: KeysView[str]) -> None:
    intersect = reserved.intersection(set(new))
    if intersect:
        raise NotImplementedError(f"some names of the given properties are reserved: {intersect}")


def not_supported(arg: Optional[Tuple[str, Any]] = None) -> None:
    # POLICY Should be called in methods in core which could be not implemented by specializations.
    frame = inspect.currentframe().f_back
    try:
        self_ = frame.f_locals["self"]
        class_name = type(self_).__name__
        method_name = inspect.getframeinfo(frame).function
        tail = f" with {arg[0]}={arg[1]}" if arg else ""
        print(f"{class_name} is not supporting {method_name}(){tail}")
    finally:
        del frame


def sort_attributes(kv: Tuple[str, str]) -> Tuple[int, str]:
    # POLICY Should be called to sort attributes of resources, templates, mappings, ...
    ordered = ["_last_action", "_validated", "_synchronized", "_store_metadata", "id", "type"]
    orders = {x: i for i, x in enumerate(ordered)}
    next_order = len(ordered) + 1
    return orders.get(kv[0], next_order), kv[0]


def repr_(obj: object) -> str:
    attributes = (f"{k}={repr(v)}" for k, v in obj.__dict__.items())
    return f"{obj.__class__.__name__}({', '.join(attributes)})"
