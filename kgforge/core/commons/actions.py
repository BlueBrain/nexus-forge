from collections import Counter
from typing import Callable, Iterable, Optional

from kgforge.core.commons.attributes import repr_
from kgforge.core.commons.typing import ManagedData
from kgforge.core.resources import Resource, Resources


def run(fun: Callable, data: ManagedData, **kwargs) -> None:
    # POLICY Should be called for operations on resources where recovering from errors is needed.
    if isinstance(data, Resources):
        for x in data:
            _run_one(fun, x, **kwargs)
        actions = Actions.from_resources(data)
        print(actions)
    elif isinstance(data, Resource):
        _run_one(fun, data, **kwargs)
        print(data._last_action)
    else:
        raise TypeError("not managed data")


def _run_one(fun: Callable, resource: Resource, **kwargs) -> None:
    # Accepted parameters:
    #   - status: Optional[str] = None
    #   - propagate: bool = False
    status = kwargs.pop("status", None)
    propagate = kwargs.pop("propagate", False)
    try:
        args = kwargs.values()
        result = fun(resource, *args)
    except Exception as e:
        status_value = False
        succeeded = False
        error = e
        error_msg = str(e)
    else:
        status_value = True if not isinstance(result, bool) else result
        succeeded = True
        error = None
        error_msg = None
    finally:
        if status:
            setattr(resource, status, status_value)
        resource._last_action = Action(fun.__name__, succeeded, error_msg)
        if propagate and error:
            raise error


class Action:

    def __init__(self, operation: str, succeeded: bool, error: Optional[str]) -> None:
        self.operation = operation
        self.succeeded = succeeded
        self.error = error

    def __repr__(self) -> str:
        return repr_(self)

    def __str__(self) -> str:
        error = f"\n<error> {self.error}" if self.error is not None else ""
        return (f"<action> {self.operation}"
                f"\n<succeeded> {self.succeeded}"
                f"{error}")

    def __eq__(self, other) -> bool:
        return self.__dict__ == other.__dict__ if type(other) is type(self) else False

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


class Actions(list):

    def __init__(self, actions: Iterable[Action]) -> None:
        super().__init__(actions)

    def __str__(self) -> str:
        counted = Counter(self)
        return "\n\n".join(f"<count> {count}\n{action}" for action, count in counted.items())

    @staticmethod
    def from_resources(resources: Resources) -> "Actions":
        return Actions(x._last_action for x in resources)


class LazyAction:

    def __init__(self, operation: Callable, *args) -> None:
        self.operation = operation
        self.args = args

    def __str__(self) -> str:
        return f"LazyAction(operation={self.operation.__qualname__}, args={list(self.args)})"

    def execute(self) -> ManagedData:
        return self.operation(*self.args)
