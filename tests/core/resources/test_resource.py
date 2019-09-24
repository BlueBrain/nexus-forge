import pytest
from pytest_bdd import given, scenarios, then, when

from kgforge.core.resources import Resource

scenarios("resource.feature")


@given("I create a resource with a property.")
def resource():
    return Resource(type="Entity")


@given("I create a resource with an other resource as property.")
def nresource():
    return Resource(type="Entity", contribution=Resource(type="Contribution"))


@when("I create a resource with a reserved attribute. Creation should fail.")
def reserved_attribute_error():
    with pytest.raises(NotImplementedError):
        Resource(_validated=True)


@then("I should be able to access it as an attribute.")
def access_property(resource):
    assert resource.type == "Entity"


@then("I should be able to access the nested resource properties as JSONPath.")
def access_nested_property(nresource):
    assert nresource.type == "Entity"
    assert nresource.contribution.type == "Contribution"
