from collections import Counter
from typing import Callable, Iterator, Optional, Sequence, Union

from kgforge.core import Resource, Resources
from kgforge.core.commons.typing import ManagedData


def run(operation: Callable, status_field: str, resource: Resource, **kwargs) -> None:
    # POLICY Should be called for operations on existing resources.
    try:
        result = operation(resource, kwargs) if kwargs else operation(resource)
    except Exception as e:
        succeeded = False
        error = str(e)
    else:
        succeeded = True
        error = None
        setattr(resource, status_field, result)
    finally:
        resource._last_action = Action(operation.__name__, succeeded, error)


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
        error = f" <error> {self.error}" if self.error is not None else ""
        return f"<action> {self.operation} <succeeded> {self.succeeded}{error}"


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
