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
    ordered = ["_last_action", "_validated", "_synchronized", "_store_metadata", "type", "id"]
    orders = {x: i for i, x in enumerate(ordered)}
    next_order = len(ordered) + 1
    return (orders.get(kv[0], next_order), kv[0])


def repr_(obj: object) -> str:
    attributes = (f"{k}={repr(v)}" for k, v in obj.__dict__.items())
    return f"{obj.__class__.__name__}({', '.join(attributes)})"
