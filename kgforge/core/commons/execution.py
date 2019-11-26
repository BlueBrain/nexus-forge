#
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

import inspect
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple, Union

from kgforge.core import Resource
from kgforge.core.commons.actions import Action, Actions, execute_lazy_actions


def not_supported(arg: Optional[Tuple[str, Any]] = None) -> None:
    # TODO When 'arg' is specified, compare with the value in the frame to know if it applies.
    # TODO If this is the case but also in general, return from the calling method.
    # POLICY Should be called in methods in core which could be not implemented by specializations.
    frame = inspect.currentframe().f_back
    try:
        self_ = frame.f_locals["self"]
        class_name = type(self_).__name__
        method_name = inspect.getframeinfo(frame).function
        tail = f" with {arg[0]}={arg[1]}" if arg else ""
        print(f"{class_name} is not supporting {method_name}(){tail}\n")
    finally:
        del frame


def catch(fun):
    # POLICY Should wrap operations on resources where recovering from errors is not needed.
    # POLICY Otherwise, use execution.run().
    @wraps(fun)
    def wrapper(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except Exception as e:
            print(f"<action> {fun.__name__}"
                  f"\n<error> {type(e).__name__}: {e}\n")
            return None
    return wrapper


# @functools.singledispatchmethod is introduced in Python 3.8.
def dispatch(data: Union[Resource, List[Resource]], fun_many: Callable,
             fun_one: Callable, *args) -> Any:
    # POLICY The method calling this function should be decorated with execution.catch().
    if isinstance(data, List) and all(isinstance(x, Resource) for x in data):
        return fun_many(data, *args)
    elif isinstance(data, Resource):
        return fun_one(data, *args)
    else:
        raise TypeError("not a Resource nor a list of Resource")


def run(fun_one: Callable, fun_many: Optional[Callable], data: Union[Resource, List[Resource]],
        **kwargs) -> None:
    # POLICY Should be called for operations on resources where recovering from errors is needed.
    status: Optional[str] = kwargs.pop("status", None)
    propagate: bool = kwargs.pop("propagate", False)
    id_required: bool = kwargs.pop("id_required", False)
    if isinstance(data, List) and all(isinstance(x, Resource) for x in data):
        if fun_many is None:
            _run_many(fun_one, data, status, propagate, id_required, **kwargs)
        else:
            fun_many(data, **kwargs)
        actions = Actions.from_resources(data)
        print(actions)
    elif isinstance(data, Resource):
        _run_one(fun_one, data, status, propagate, id_required, **kwargs)
        action = data._last_action
        print(action)
    else:
        raise TypeError("not a Resource nor a list of Resource")


def _run_many(fun: Callable, resources: List[Resource], status: Optional[str], propagate: bool,
              id_required: bool, **kwargs) -> None:
    for x in resources:
        _run_one(fun, x, status, propagate, id_required, **kwargs)


def _run_one(fun: Callable, resource: Resource, status: Optional[str], propagate: bool,
             id_required: bool, **kwargs) -> None:
    try:
        if id_required and not hasattr(resource, "id"):
            raise Exception("resource does not have an id")
        execute_lazy_actions(resource)
        result = fun(resource, **kwargs)
    except Exception as e:
        status_value = False
        succeeded = False
        error = e
    else:
        status_value = True if not isinstance(result, bool) else result
        succeeded = True
        error = None
    finally:
        if status:
            setattr(resource, status, status_value)
        resource._last_action = Action(fun.__name__, succeeded, error)
        if propagate and error:
            raise error
