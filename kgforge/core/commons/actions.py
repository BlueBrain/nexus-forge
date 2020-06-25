# 
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.

from collections import Counter
from typing import Any, Callable, Iterable, Iterator, List, Optional, Union

from kgforge.core import Resource
from kgforge.core.commons.attributes import eq_class, repr_class


class Action:

    def __init__(self, operation: str, succeeded: bool, error: Optional[Exception]) -> None:
        self.operation: str = operation
        self.succeeded: bool = succeeded
        self.error: Optional[str] = type(error).__name__ if error else None
        self.message: Optional[str] = str(error) if error else None

    def __repr__(self) -> str:
        return repr_class(self)

    def __str__(self) -> str:
        error = f"\n<error> {self.error}: {self.message}" if self.error is not None else ""
        return (f"<action> {self.operation}"
                f"\n<succeeded> {self.succeeded}"
                f"{error}")

    def __eq__(self, other: object) -> bool:
        return eq_class(self, other)

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


class Actions(list):

    def __init__(self, actions: Iterable[Action]) -> None:
        super().__init__(actions)

    # No need to define __repr__ as the one from list are suitable.

    def __str__(self) -> str:
        counted = Counter(self)
        return "\n\n".join(f"<count> {count}\n{action}" for action, count in counted.items())

    @staticmethod
    def from_resources(resources: List[Resource]):
        return Actions(x._last_action for x in resources)


class LazyAction:

    def __init__(self, operation: Callable, *args) -> None:
        self.operation: Callable = operation
        self.args = args

    def __repr__(self) -> str:
        return repr_class(self)

    def __str__(self) -> str:
        return f"LazyAction(operation={self.operation.__qualname__}, args={list(self.args)})"

    def __eq__(self, other: object) -> bool:
        return eq_class(self, other)

    def execute(self) -> Union[Resource, List[Resource]]:
        # POLICY Operation should propagate exceptions. This is for actions.execute_lazy_actions().
        return self.operation(*self.args)


def execute_lazy_actions(resource: Resource, lazy_actions: List[str]) -> None:
    # TODO Use as base an implementation of JSONPath for Python. DKE-147.
    for path in lazy_actions:
        lazy_action = eval(path, {}, {"x": resource})
        result = lazy_action.execute()
        rc_path, rc_prop = path.rsplit(".", maxsplit=1)
        rc = eval(rc_path, {}, {"x": resource})
        if not rc_prop.endswith("]"):
            setattr(rc, rc_prop, result)
        else:
            exec(f"{path} = result", {}, {"x": resource, "result": result})


def collect_lazy_actions(resource: Resource) -> List[str]:
    return list(_collect_lazy_actions(resource, "x"))


def _collect_lazy_actions(data: Any, root: str) -> Iterator[str]:
    if isinstance(data, Resource):
        for k, v in data.__dict__.items():
            path = f"{root}.{k}"
            if isinstance(v, List):
                for i, x in enumerate(v):
                    if isinstance(x, LazyAction):
                        yield f"{path}[{i}]"
                    else:
                        yield from _collect_lazy_actions(x, f"{path}[{i}]")
            elif isinstance(v, Resource):
                yield from _collect_lazy_actions(v, path)
            elif isinstance(v, LazyAction):
                yield path
