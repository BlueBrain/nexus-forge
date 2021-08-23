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

import pytest
from pytest_bdd import given, scenarios, then, when

from kgforge.core import Resource

# TODO To be port to the generic parameterizable test suite for resources in test_resources.py.
#  DKE-135.
from kgforge.core.resource import encode

scenarios("resource.feature")


@given("I create a resource with a property.")
def resource():
    return Resource(type="Entity")


@given("I create a resource from a JSON dict.")
def resource_from_json(json_one):
    return Resource.from_json(json_one)


@given("I create a resource from a JSON dict and exclude fields.")
def resource_from_json_na_one(json_one):
    return Resource.from_json(json_one, na="v1a")


@given("I create a resource from a JSON dict and exclude fields.")
def resource_from_json_na_many(json_one):
    return Resource.from_json(json_one, na=["v1a","v2a"])


@given("I create a resource with an other resource as property.")
def nresource():
    return Resource(type="Entity", contribution=Resource(type="Contribution"))


@when("I create a resource with a reserved attribute. Creation should fail.")
def reserved_attribute_error():
    with pytest.raises(NotImplementedError):
        Resource(_validated=True)


@then("I should be able to access properties as object attribute.")
def access_property(resource, resource_from_json, resource_from_json_na_one, resource_from_json_na_many):
    assert resource.type == "Entity"
    assert list(encode(resource_from_json).keys()) == ["id","type","p1","p2"]
    assert list(encode(resource_from_json).values()) == ["123","Type","v1a","v2a"]
    assert list(encode(resource_from_json_na_one).keys()) == ["id","type","p2"]
    assert list(encode(resource_from_json_na_one).values()) == ["123","Type","v2a"]
    assert list(encode(resource_from_json_na_many).keys()) == ["id","type"]
    assert list(encode(resource_from_json_na_many).values()) == ["123","Type"]


@then("I should be able to access the nested resource properties as JSONPath.")
def access_nested_property(nresource):
    assert nresource.type == "Entity"
    assert nresource.contribution.type == "Contribution"
