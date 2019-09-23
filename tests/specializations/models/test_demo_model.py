from pytest_bdd import given, parsers, scenarios, when

from kgforge.specializations.models.demo_model import DemoModel
from tests.conftest import check_report

scenarios("demo_model.feature")


@given("A model instance.")
def model():
    # TODO Tests for 'Model data could be loaded from an URL or the store'.
    return DemoModel("./specializations/models/demo_model_data/")


@given("A validated resource.", target_fixture="data")
def validated_resource(model, valid_resource):
    model.validate(valid_resource)
    assert valid_resource._validated == True
    return valid_resource


@when(parsers.re("I validate the resource(?P<rc>s?)."
                 " The printed report does(?P<err> not)? mention an error(: '(?P<msg>[a-zA-Z0-9 ]+)')?."))
def validate(capsys, model, data, rc, err, msg):
    model.validate(data)
    check_report(capsys, rc, err, msg, "_validate")


@when("I validate the resource. An exception is raised. The printed report mentions an error: 'exception raised'.")
def validate_exception(monkeypatch, capsys, model, data):
    def _validate(_, x): raise Exception("exception raised")
    monkeypatch.setattr("kgforge.specializations.models.demo_model.DemoModel._validate", _validate)
    model.validate(data)
    out = capsys.readouterr().out[:-1]
    assert out == f"<action> _validate\n<succeeded> False\n<error> exception raised"
