from collections import Counter
from typing import Callable, Iterator

from kgforge.core import Resource, Resources


def _run(fun: Callable, status_field: str, resource: Resource) -> None:
    try:
        result = fun(resource)
    except Exception as e:
        succeeded = False
        error = str(e)
    else:
        succeeded = True
        error = None
        setattr(resource, status_field, result)
    finally:
        resource._last_action = Action(fun.__name__, succeeded, error)


class Action:

    def __init__(self, type: str, succeeded: bool, error: str) -> None:
        self.type = type
        self.succeeded = succeeded
        self.error = error

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __str__(self) -> str:
        return _str(self)


# FIXME Check if inheriting directly from 'list' is a good idea.
class Actions(list):

    def __init__(self, actions: Iterator[Action]) -> None:
        super().__init__(actions)

    def __str__(self):
        counted = Counter(self)
        return "\n".join(f"<count> {count} {_str(action)}" for action, count in counted.items())

    @staticmethod
    def from_resources(resources: Resources) -> "Actions":
        return Actions(x._last_action for x in resources)


def _str(action: Action) -> str:
    error = f" <error> {action.error}" if action.error is not None else ""
    return f"<action> {action.type} <succeeded> {action.succeeded}{error}"


class LazyAction:

    def __init__(self) -> None:
        print("FIXME - LazyAction")
