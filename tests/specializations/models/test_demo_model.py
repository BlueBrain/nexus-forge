from typing import Callable

import pytest
from pytest import fixture
from pytest_bdd import given, parsers, scenarios, then, when, scenario

from kgforge.core.commons.actions import Action
from kgforge.core.commons.typing import ManagedData
from kgforge.core.resources import Resource, Resources
from kgforge.specializations.models.demo_model import DemoModel
from tests.conftest import resource, resources, check


scenarios("demo_model.feature")


@given("A model instance.")
def model():
    # FIXME Should test the loading from a directory, an URL, or the store.
    return DemoModel("./demo-model/")


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


@given("A validated resource.", target_fixture="data")
def validated_resource(model, valid_resource):
    model.validate(valid_resource)
    assert valid_resource._validated == True
    return valid_resource


@when(parsers.re("I validate the resource(?P<one_or_many>s?)."
                 " The report should be printed (?P<with_or_without>[a-z]+) (the|an)"
                 " error( '(?P<error_message>([a-zA-Z0-9 ]+))')?."))
def validate(capsys, model, data, one_or_many, with_or_without, error_message):
    model.validate(data)
    out = capsys.readouterr().out[:-1]
    if one_or_many == "":
        head = ""
    elif one_or_many == "s":
        head = "<count> 2\n"
    else:
        raise ValueError
    if with_or_without == "with":
        tail = f"False\n<error> {error_message}"
    elif with_or_without == "without":
        tail = "True"
    else:
        raise ValueError
    assert out == f"{head}<action> _validate\n<succeeded> {tail}"


@when("I validate the resource. An exception is raised. The report should be printed with the error 'exception raised'.")
def validate_resource_exception(monkeypatch, capsys, model, data):
    def _validate(_, x): raise Exception("exception raised")
    monkeypatch.setattr("kgforge.specializations.models.demo_model.DemoModel._validate", _validate)
    model.validate(data)
    out = capsys.readouterr().out[:-1]
    assert out == f"<action> _validate\n<succeeded> False\n<error> exception raised"


@when("I modify the resource.")
def modify_resource(data):
    data.name = "other"


@then(parsers.parse("The validation status of {} resource should be {value}."))
def check_validation_status(data, value):
    def fun(x): assert str(x._validated) == value
    check(fun, data)


@then("I should be able to access the report of the action on a resource.")
def check_validate_action(data):
    def fun(x): assert isinstance(x._last_action, Action)
    check(fun, data)


@then(parsers.parse("The report should say that the operation was '{value}'."))
def check_validate_action_operation(data, value):
    def fun(x): assert x._last_action.operation == value
    check(fun, data)


@then(parsers.parse("The report should say that the operation success is: {value}."))
def check_validate_action_success(data, value):
    def fun(x): assert str(x._last_action.succeeded) == value
    check(fun, data)


@then(parsers.parse("The report should say that the error was '{value}'."))
def check_validate_action_error(data, value):
    def fun(x): assert str(x._last_action.error) == value
    check(fun, data)
