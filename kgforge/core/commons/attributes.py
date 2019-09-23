import inspect
from typing import Any, KeysView, Optional, Set, Tuple


def check_collisions(reserved: Set[str], new: KeysView[str]) -> None:
    intersect = reserved.intersection(set(new))
    if intersect:
        raise NotImplementedError(f"Some names of the given properties are reserved: {intersect}")


def not_supported(arg: Optional[Tuple[str, Any]] = None) -> None:
    # POLICY Should be called in methods in core which could be not implemented by specializations.
    frame = inspect.currentframe().f_back
    try:
        class_name = type(frame.f_locals["self"]).__name__
        method_name = inspect.getframeinfo(frame).function
        tail = f" with {arg[0]}={arg[1]}" if arg else ""
        print(f"{class_name} is not supporting {method_name}(){tail}")
    finally:
        del frame


def repr_(obj: object) -> str:
    attributes = (f"{k}={repr(v)}" for k, v in obj.__dict__.items())
    return f"{obj.__class__.__name__}({', '.join(attributes)})"
