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

from pytest_bdd import given, parsers, scenarios, then, when

from kgforge.core.commons.typing import do
from kgforge.specializations.stores.demo_store import DemoStore
from tests.conftest import check_report

scenarios("demo_store.feature")


@given("A store instance.")
def store():
    return DemoStore()


@given("An already registered resource.", target_fixture="data")
def registered_resource(store, valid_resource):
    store.register(valid_resource, False)
    assert valid_resource._synchronized == True
    return valid_resource


@given("Already registered resources.", target_fixture="data")
def registered_resources(store, valid_resources):
    store.register(valid_resources, False)
    for x in valid_resources:
        assert x._synchronized == True
        assert x._store_metadata == {'version': 1, 'deprecated': False}
    return valid_resources


@when(parsers.re("I register the resource(?P<rc>s?)."
                 " The printed report does(?P<err> not)? mention an error(: '(?P<msg>[a-zA-Z0-9 ]+)')?."))
def register(capsys, store, data, rc, err, msg):
    store.register(data, False)
    check_report(capsys, rc, err, msg, "_register")


@when("I register the resource. An exception is raised. The printed report does mention an error: 'exception raised'.")
def register_exception(monkeypatch, capsys, store, data):
    def _register(_, x, y): raise Exception("exception raised")
    monkeypatch.setattr("kgforge.specializations.stores.demo_store.DemoStore._register", _register)
    store.register(data, False)
    out = capsys.readouterr().out[:-1]
    assert out == f"<action> _register\n<succeeded> False\n<error> exception raised"


@then(parsers.parse("The store metadata of a resource should be '{metadata}'."))
def check_metadata(data, metadata):
    def fun(x): assert str(x._store_metadata) == metadata
    do(fun, data, error=True)
