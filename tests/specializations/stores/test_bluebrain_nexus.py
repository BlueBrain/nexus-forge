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

import os

import pytest
from typing import Callable, Union, List

from unittest import mock

from kgforge.core.archetypes import Store
from kgforge.core.wrappings.dict import wrap_dict
from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus
from kgforge.specializations.stores.nexus.service import to_resource
from tests.data import *

# TODO To be port to the generic parameterizable test suite for stores in test_stores.py. DKE-135.


BUCKET = "test/kgforge"
NEXUS = "https://nexus-instance.org/"
TOKEN = "token"

VERSIONED_TEMPLATE = "{x.id}?rev={x._store_metadata._rev}"
FILE_RESOURCE_MAPPING = os.sep.join((os.path.curdir, "tests", "data", "nexus-store",
                                     "file-to-resource-mapping.hjson"))

NEXUS_PROJECT_CONTEXT = {"base": "http://data.net/", "vocab": "http://vocab.net/"}


@pytest.fixture
@mock.patch('nexussdk.projects.fetch', return_value=NEXUS_PROJECT_CONTEXT)
def nexus_store(nexus_patch):
    # FIXME mock Nexus for unittests
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token=TOKEN,
                          file_resource_mapping=FILE_RESOURCE_MAPPING,
                          versioned_id_template=VERSIONED_TEMPLATE)


@pytest.fixture
def nested_resource():
    contributions = [Resource(title=f"contribution {i}") for i in range(3)]
    return Resource(type="Agent", name="someone", contributions=contributions)


@pytest.fixture
def nested_registered_resource(nested_resource):
    ingredients = [Resource(id=i, type='Ingredient') for i in range(3)]
    resource = Resource(id="a_recipe", type="Recipe", ingridients=ingredients,
                        author=Resource(id="a_person", type="Person"))
    do_recursive(add_metadata, resource)
    return resource


def test_config_error():
    with pytest.raises(ValueError):
        BlueBrainNexus(endpoint="test", bucket="invalid", token="")


def test_config(nexus_store):
    assert nexus_store.organisation == "test"
    assert nexus_store.project == "kgforge"
    assert nexus_store.endpoint == NEXUS


def test_freeze_fail(nexus_store: Store, nested_resource):
    """nested resource is not registered, thus freeze will fail"""
    nexus_store.versioned_id_template = "{x.id}?rev={x._store_metadata._rev}"
    nested_resource.id = "abc"
    add_metadata(nested_resource)


def test_freeze_nested(nexus_store: Store, nested_registered_resource):
    nexus_store.versioned_id_template = "{x.id}?rev={x._store_metadata._rev}"
    nexus_store.freeze(nested_registered_resource)
    do_recursive(check_frozen_id, nested_registered_resource)


@pytest.mark.parametrize("data, expected", [
    pytest.param(JSON_LD_1, RESOURCE_1, id="standard-json-ld"),
    pytest.param(JSON_LD_2, RESOURCE_2, id="no-context-"),
    pytest.param(JSON_LD_3, RESOURCE_3, id="local-context-list-1"),
    pytest.param(JSON_LD_5, RESOURCE_5, id="context-and-meta")
])
def test_to_resource(data, expected):
    resource = to_resource(data)
    assert_equal(expected, resource), "resource is not as the expected"


def assert_equal(first, second):
    assert str(first) == str(second)
    assert getattr(first, "_context", None) == getattr(first, "_context", None)


def check_frozen_id(resource: Resource):
    assert resource.id.endswith('?rev=' + str(resource._store_metadata['_rev']))


def add_metadata(resource: Resource):
    metadata = {
        "_self": resource.id,
        "_constrainedBy": "https://bluebrain.github.io/nexus/schemas/unconstrained.json",
        "_project": "https://nexus/org/prj",
        "_rev": 1,
        "_deprecated": False,
        "_createdAt": "2019-03-28T13:40:38.934Z",
        "_createdBy": "https://nexus/u1",
        "_updatedAt": "2019-03-28T13:40:38.934Z",
        "_updatedBy": "https://nexus/u1",
        "_incoming": "https:/nexus/incoming",
        "_outgoing": "https://nexux/outgoing"
    }
    resource._synchronized = True
    resource._validated = True
    resource._store_metadata = wrap_dict(metadata)


def add_meta(r, m):
    r._store_metadata = wrap_dict(m)


def do_recursive(fun: Callable, data: Union[Resource, List[Resource]], *args) -> None:
    if isinstance(data, List) and all(isinstance(x, Resource) for x in data):
        for x in data:
            fun(x, *args)
    elif isinstance(data, Resource):
        fun(data, *args)
        for _, v in data.__dict__.items():
            if isinstance(v, (Resource, List)):
                do_recursive(fun, v, *args)
    else:
        raise TypeError("not a Resource nor a list of Resource")
