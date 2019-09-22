from typing import Callable

from kgforge.core.commons.typing import ManagedData
from kgforge.core.resources import Resource, Resources


def check(fun: Callable, data: ManagedData):
    fun(data) if not isinstance(data, Resources) else (fun(x) for x in data)


def resource(valid: bool, index: int = 0) -> Resource:
    r = Resource(type="Person")
    if valid:
        r.name = f"resource {index}"
    return r


def resources(valid: bool) -> Resources:
    r1 = resource(valid, 0)
    r2 = resource(valid, 1)
    return Resources(r1, r2)
