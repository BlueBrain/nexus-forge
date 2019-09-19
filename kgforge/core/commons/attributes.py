import inspect
from typing import Any, KeysView, List, Set


def check_collisions(reserved: Set[str], new: KeysView[str]) -> None:
    intersect = reserved.intersection(set(new))
    if intersect:
        raise NotImplementedError(f"Some names of the given properties are reserved: {intersect}")


def safe_setattr(object: Any, name: str, value: Any) -> None:
    if hasattr(object, name):
        raise NotImplementedError(f"Name of the property is reserved: {name}")
    else:
        setattr(object, name, value)


def not_supported() -> None:
    # POLICY Should be called in methods in core which could be not implemented by specializations.
    frame = inspect.currentframe().f_back
    try:
        class_name = type(frame.f_locals["self"]).__name__
        method_name = inspect.getframeinfo(frame).function
        print(f"{class_name} is not supporting {method_name}")
    finally:
        del frame


def as_list(data: Any) -> List[Any]:
    return [data] if not isinstance(data, list) else data
