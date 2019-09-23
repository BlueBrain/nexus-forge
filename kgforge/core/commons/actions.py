from collections import Counter
from typing import Callable, Iterator, Optional, Sequence, Union

from kgforge.core.commons.attributes import repr_
from kgforge.core.commons.typing import ManagedData
from kgforge.core.resources import Resource, Resources


def run(fun: Callable, data: ManagedData, status_attr: Optional[str],  *args) -> None:
    # POLICY Should be called for operations on resources.
    if isinstance(data, Resources):
        for x in data:
            _run_one(fun, x, status_attr, *args)
        print(Actions.from_resources(data))
    elif isinstance(data, Resource):
        _run_one(fun, data, status_attr, *args)
        print(data._last_action)
    else:
        raise TypeError("Not managed data")


def _run_one(fun: Callable, resource: Resource, status_attr: Optional[str],  *args) -> None:
    try:
        result = fun(resource, *args)
    except Exception as e:
        status_value = False
        succeeded = False
        error = str(e)
    else:
        status_value = True if not isinstance(result, bool) else result
        succeeded = True
        error = None
    finally:
        if status_attr:
            setattr(resource, status_attr, status_value)
        resource._last_action = Action(fun.__name__, succeeded, error)


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

    def __init__(self, actions: Union[Sequence[Action], Iterator[Action]]) -> None:
        super().__init__(actions)

    def __str__(self) -> str:
        counted = Counter(self)
        return "\n\n".join(f"<count> {count}\n{action}" for action, count in counted.items())

    @staticmethod
    def from_resources(resources: Resources) -> "Actions":
        return Actions(x._last_action for x in resources)


class LazyAction:

    def __init__(self, operation: Callable, **params) -> None:
        self.operation = operation
        self.params = params

    def execute(self) -> ManagedData:
        return self.operation(self.params)
