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

import hjson
import pytest

from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.exceptions import FreezingError
from kgforge.core.wrappings.dict import wrap_dict
from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus
from tests.data import *

# TODO To be port to the generic parameterizable test suite for stores in test_stores.py.


BUCKET = "test/kgforge"
NEXUS = "https://nexus-instance.org/"
TOKEN = "token"


@pytest.fixture
def nexus_store():
    # FIXME mock Nexus for unittests
    file_to_resource_mapping = os.sep.join(
        (os.path.curdir, "tests", "data", "nexus-store", "file-to-resource-mapping.hjson"))
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token=TOKEN,
                          file_resource_mapping=file_to_resource_mapping)


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


# FIXME Migrate to v0.2.0.
# def test_freeze_fail(nexus_store, nested_resource):
#     with pytest.raises(FreezingError):
#         nested_resource.id = "abc"
#         nexus_store.freeze(nested_resource)


# FIXME Migrate to v0.2.0.
# def test_freeze_nested(nexus_store, nested_registered_resource):
#     nexus_store.freeze(nested_registered_resource)
#     check_frozen_id(nested_registered_resource)
#     for k, v in nested_registered_resource.__dict__.items():
#         if isinstance(v, list):
#             for r in v:
#                 do(check_frozen_id, r, False)
#         else:
#             do(check_frozen_id, v, False)


@pytest.mark.parametrize("data, expected", [
    pytest.param(JSON_LD_1, RESOURCE_1, id="standard-json-ld"),
    pytest.param(JSON_LD_2, RESOURCE_2, id="no-context-"),
    pytest.param(JSON_LD_3, RESOURCE_3, id="local-context-list-1"),
    pytest.param(JSON_LD_5, RESOURCE_5, id="context-and-meta")
])
def test_response_to_resource(nexus_store, data, expected):
    resource = nexus_store._to_resource(data)
    assert_equal(expected, resource), "resource is not as the expected"


# FIXME Migrate to v0.2.0.
# def test_extract_properties(nexus_store):
#     simple = Resource(type="Experiment", url="file.gz")
#     r = nexus_store._collect_files(simple, "url")
#     assert simple.url in r, "url should be in the list"
#     deep = Resource(type="Experiment", level1=Resource(level2=Resource(url="file.gz")))
#     r = nexus_store._collect_files(deep, "level1.level2.url")
#     assert deep.level1.level2.url in r, "url should be in the list"
#     files = Resources([Resource(type="Experiment", url=f"file{i}") for i in range(3)])
#     r = nexus_store._collect_files(files, "url")
#     assert ["file0", "file1", "file2"] == r, "three elements should be in the list"
#     data_set = Resource(type="Dataset", hasPart=files)
#     r = nexus_store._collect_files(data_set, "hasPart.url")
#     assert ["file0", "file1", "file2"] == r, "three elements should be in the list"
#     r = nexus_store._collect_files(data_set, "fake.path")
#     assert len(r) == 0, "list is empty"


# FIXME Migrate to v0.2.0.
# def test_collect_lazy_actions(nexus_store):
#     resource = Resource(file1=LazyAction(None),
#                         level2=Resources(
#                             [Resource(file2=LazyAction(None)), Resource(file3=LazyAction(None))]))
#     actions = nexus_store._collect_lazy_actions(resource)
#     assert len(actions) == 3, "there should be three lazzy actions"


# FIXME Migrate to v0.2.0.
# def test_resolve_file_resource_mapping_from_file(nexus_store):
#     mapping = hjson.loads(str(nexus_store._resolve_file_resource_mapping()))
#     assert mapping["type"] == "DataDownload"


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
    r._store_metadata = wrap_dict(m)
