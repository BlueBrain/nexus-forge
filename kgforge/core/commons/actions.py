from collections import Counter
from typing import Any, Callable, Iterator, Optional, Sequence, Union

from kgforge.core import Resource, Resources
from kgforge.core.commons.typing import ManagedData


def run(fun: Callable, status_attr: str, resource: Resource, *args) -> Any:
    # POLICY Should be called for operations on resources.
    try:
        result = fun(resource, *args)
    except Exception as e:
        status_value = False
        has_raised = True
        error = str(e)
    else:
        status_value = True if not isinstance(result, bool) else result
        has_raised = False
        error = None
    finally:
        setattr(resource, status_attr, status_value)
        resource._last_action = Action(fun.__name__, has_raised, error)
        return result


class Action:

    def __init__(self, operation: str, succeeded: bool, error: Optional[str]) -> None:
        self.operation = operation
        self.succeeded = succeeded
        self.error = error

    def __str__(self) -> str:
        return self._str()

    def __eq__(self, other) -> bool:
        return self.__dict__ == other.__dict__ if type(other) is type(self) else False

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))

    def _str(self) -> str:
        error = f"\n<error> {self.error}" if self.error is not None else ""
        return (f"<action> {self.operation}"
                f"\n<succeeded> {self.succeeded}"
                f"{error}")


class Actions(list):

    def __init__(self, actions: Union[Sequence[Action], Iterator[Action]]) -> None:
        super().__init__(actions)

    def __str__(self) -> str:
        counted = Counter(self)
        return "\n".join(f"<count> {count} {action}" for action, count in counted.items())

    @staticmethod
    def from_resources(resources: Resources) -> "Actions":
        return Actions(x._last_action for x in resources)


class LazyAction:

    def __init__(self, operation: Callable, **params) -> None:
        self.operation = operation
        self.params = params

    def execute(self) -> ManagedData:
        return self.operation(self.params)
