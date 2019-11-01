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

import pytest
from kgforge.core import Resources

from kgforge.core.commons.typing import do
from kgforge.core.commons.wrappers import DictWrapper
from kgforge.core.storing.exceptions import FreezingError
from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus
from tests.data import *

BUCKET = "test/kgforge"
NEXUS = "https://nexus-instance.org/"
TOKEN = "token"

@pytest.fixture
def nexus_store():
    # FIXME mock Nexus for unittests
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token=TOKEN)


@pytest.fixture
def nexus_store_unauthorized():
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token="invalid token")


@pytest.fixture
def nested_resource():
    contributions = Resources([Resource(title=f"contribution {i}") for i in range(3)])
    return Resource(type="Agent", name="someone", contributions=contributions)


@pytest.fixture
def nested_registered_resource(nested_resource):
    ingredients = Resources([Resource(id=i, type='Ingredient') for i in range(3)])
    resource = Resource(id="a_recipe", type="Recipe", ingridients=ingredients,
                        author=Resource(id="a_person", type="Person"))
    add_meta_recursive(resource)
    return resource


def test_config_error():
    with pytest.raises(ValueError):
        BlueBrainNexus(endpoint="test", bucket="invalid", token="")


def test_config(nexus_store):
    assert nexus_store.organisation == "test"
    assert nexus_store.project == "kgforge"
    assert nexus_store.endpoint == NEXUS


def test_freeze_fail(nexus_store, nested_resource):
    with pytest.raises(FreezingError):
        nested_resource.id = "abc"
        nexus_store.freeze(nested_resource)


def test_freeze_nested(nexus_store, nested_registered_resource):
    nexus_store.freeze(nested_registered_resource)
    check_frozen_id(nested_registered_resource)
    for k, v in nested_registered_resource.__dict__.items():
        if isinstance(v, list):
            for r in v:
                do(check_frozen_id, r, False)
        else:
            do(check_frozen_id, v, False)


@pytest.mark.parametrize("data, expected", [
    pytest.param(JSON_LD_1, RESOURCE_1, id="standard-json-ld"),
    pytest.param(JSON_LD_2, RESOURCE_2, id="no-context-"),
    pytest.param(JSON_LD_3, RESOURCE_3, id="local-context-list-1"),
    pytest.param(JSON_LD_5, RESOURCE_5, id="context-and-meta")
])
def test_response_to_resource(nexus_store, data, expected):
    resource = nexus_store._to_resource(data)
    assert_equal(expected, resource), "resource is not as the expected"


def assert_equal(first, second):
    assert str(first) == str(second)
    assert getattr(first, "_context", None) == getattr(first, "_context", None)


def check_frozen_id(resource: Resource):
    assert resource.id.endswith('?rev=' + str(resource._store_metadata['_rev']))


def add_meta_recursive(resource: Resource):
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
    add_meta(resource, metadata)
    for k, v in resource.__dict__.items():
        if isinstance(v, list):
            for elem in v:
                do(add_meta, elem, False, metadata)
        else:
            do(add_meta, v, False, metadata)


def add_meta(r, m):
    r._store_metadata = DictWrapper._wrap(m)
