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

from typing import Callable, List, Union
from uuid import uuid4

from pytest_bdd import given, parsers, then, when

from kgforge.core import Resource
from kgforge.core.commons.actions import Action


def do(fun: Callable, data: Union[Resource, List[Resource]], *args) -> None:
    if isinstance(data, List) and all(isinstance(x, Resource) for x in data):
        for x in data:
            fun(x, *args)
    elif isinstance(data, Resource):
        fun(data, *args)
    else:
        raise TypeError("not a Resource nor a list of Resource")


# It seems using 'given' with both 'fixture' and 'target_fixture' does not work.
# This implies that (in)valid resources creation steps need their dedicated function.


# Resource(s) creation.

def resource(valid: bool, index: int = 0) -> Resource:
    rid = str(uuid4())
    r = Resource(type="Person", id=rid)
    if valid:
        r.name = f"resource {index}"
    return r


def resources(valid: bool) -> List[Resource]:
    r1 = resource(valid, 0)
    r2 = resource(valid, 1)
    return [r1, r2]


@given("A valid resource.", target_fixture="data")
def valid_resource():
    return resource(True)


@given("Valid resources.", target_fixture="data")
def valid_resources():
    return resources(True)


@given("An invalid resource.", target_fixture="data")
def invalid_resource():
    return resource(False)


@given("Invalid resources.", target_fixture="data")
def invalid_resources():
    return resources(False)


# Resource(s) modifications.

@when("I modify the resource.")
def modify_resource(data):
    data.name = "other"


# Resource(s) verifications.

@then(parsers.parse("The '{attr}' status of {} resource should be '{value}'."))
def check_resource_status(data, attr, value):
    def fun(x): assert str(getattr(x, attr)) == value
    do(fun, data)


# Action(s) verifications.

def check_report(capsys, rc, err, msg, op):
    out = capsys.readouterr().out[:-1]
    heads = {
        "": "",
        "s": "<count> 2\n",
    }
    head = heads[rc]
    tails = {
        None: f"False\n<error> {msg}",
        " not": "True",
    }
    tail = tails[err]
    assert out == f"{head}<action> {op}\n<succeeded> {tail}"


@then("I should be able to access the report of the action on a resource.")
def check_action(data):
    def fun(x): assert isinstance(x._last_action, Action)
    do(fun, data)


@then(parsers.parse("The report should say that the operation was '{value}'."))
def check_action_operation(data, value):
    def fun(x): assert x._last_action.operation == value
    do(fun, data)


@then(parsers.parse("The report should say that the operation success is '{value}'."))
def check_action_success(data, value):
    def fun(x): assert str(x._last_action.succeeded) == value
    do(fun, data)


@then(parsers.parse("The report should say that the error was '{value}'."))
def check_action_error(data, value):
    def fun(x): assert str(x._last_action.error) == value
    do(fun, data)
