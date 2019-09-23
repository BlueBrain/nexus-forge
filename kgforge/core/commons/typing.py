from typing import Any, Callable, List, Union

from kgforge.core.resources import Resource, Resources

DirPath = str
FilePath = str

IRI = str
URL = str

Hjson = str

ManagedData = Union[Resource, Resources]


# @functools.singledispatchmethod is introduced in Python 3.8.
def dispatch(data: ManagedData, fun_resources: Callable, fun_resource: Callable, *args) -> Any:
    if isinstance(data, Resources):
        return fun_resources(data, *args)
    elif isinstance(data, Resource):
        return fun_resource(data, *args)
    else:
        raise TypeError("Not managed data")


def as_list_if_not(data: Any) -> List[Any]:
    return [data] if not isinstance(data, list) else data
