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
    return Resource(type="Entity", contribution=Resource(type="Contribution"),
                    used=[Resource(type="Entity"), Resource(type="Dataset")])

@given("I create a resource with an id and type.")
def resource_id_type():
    return Resource(id="https://id", type="Person", name="name")


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
    assert nresource.used[0].type == "Entity"
    assert nresource.used[1].type == "Dataset"


@then("I assigned _synchronized to True so the resource should give _inner_sync equals True.")
def change_property(resource):
    resource._synchronized = True
    assert resource._inner_sync == True
    resource.type = "test"
    assert resource._synchronized == False


@then("I changed a nested property so the resource should give _synchronized equals False.")
def change_nested_property(nresource):
    nresource._synchronized = True 
    assert nresource._inner_sync == True
    # Change some property
    nresource.contribution.type = "test"
    assert nresource._synchronized == False
    assert nresource._inner_sync == False
    # Synchronize again
    nresource._synchronized = True 
    assert nresource._inner_sync == True
    # Change a list
    for u in nresource.used:
        u.value = 10
    assert nresource._synchronized == False
    assert nresource._inner_sync == False

@then("I should be able to get its type and identifier.")
def change_nested_property(resource_id_type):
    assert resource_id_type.has_identifier(return_attribute=True) == (True, "id")
    assert resource_id_type.has_identifier() is True
    assert resource_id_type.has_type(return_attribute=True) == (True, "type")
    assert resource_id_type.has_type() is True
    
    assert resource_id_type.get_identifier() == "https://id"
    assert resource_id_type.get_type() == "Person"

    resource_no_id_no_type = Resource(name="name")
    assert resource_no_id_no_type.has_identifier(return_attribute=True) == (False, None)
    assert resource_no_id_no_type.has_identifier() is False
    assert resource_no_id_no_type.has_type(return_attribute=True) == (False, None)
    assert resource_no_id_no_type.has_type() is False
    
    assert resource_no_id_no_type.get_identifier() is None
    assert resource_no_id_no_type.get_type() is None

    
