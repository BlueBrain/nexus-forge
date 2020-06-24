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

from pytest_bdd import given, parsers, scenarios, when

from kgforge.specializations.models.demo_model import DemoModel
from tests.conftest import check_report

# TODO To be port to the generic parameterizable test suite for models in test_models.py. DKE-135.


scenarios("demo_model.feature")


@given("A model instance.")
def model():
    return DemoModel("tests/data/demo-model/", origin="directory")


@given("A validated resource.", target_fixture="data")
def validated_resource(model, valid_resource):
    model.validate(valid_resource, execute_actions_before=False)
    assert valid_resource._validated == True
    return valid_resource


@when(parsers.re("I validate the resource(?P<rc>s?)."
                 " The printed report does(?P<err> not)? mention an error(: '(?P<msg>[a-zA-Z0-9: ]+)')?."))
def validate(capsys, model, data, rc, err, msg):
    model.validate(data, execute_actions_before=False)
    check_report(capsys, rc, err, msg, "_validate_one")


@when("I validate the resource. An exception is raised. The printed report mentions an error: 'Exception: exception raised'.")
def validate_exception(monkeypatch, capsys, model, data):
    def _validate_one(_, x): raise Exception("exception raised")
    monkeypatch.setattr("kgforge.specializations.models.demo_model.DemoModel._validate_one", _validate_one)
    model.validate(data, execute_actions_before=False)
    out = capsys.readouterr().out[:-1]
    assert out == f"<action> _validate_one\n<succeeded> False\n<error> Exception: exception raised"
