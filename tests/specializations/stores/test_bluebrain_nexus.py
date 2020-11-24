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

import os
from unittest import mock
from urllib.parse import urljoin
from urllib.request import pathname2url
from uuid import uuid4

import nexussdk
import pytest
from typing import Callable, Union, List

from kgforge.core import Resource
from kgforge.core.archetypes import Store
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import _merge_jsonld
from kgforge.core.wrappings.dict import wrap_dict
from kgforge.core.wrappings.paths import Filter
from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus, build_query_statements

# FIXME mock Nexus for unittests
# TODO To be port to the generic parameterizable test suite for stores in test_stores.py. DKE-135.
from kgforge.specializations.stores.nexus.service import NEXUS_CONTEXT

BUCKET = "test/kgforge"
NEXUS = "https://nexus-instance.org/"
TOKEN = "token"
NEXUS_PROJECT_CONTEXT = {"base": "http://data.net/", "vocab": "http://vocab.net/"}

VERSIONED_TEMPLATE = "{x.id}?rev={x._store_metadata._rev}"
FILE_RESOURCE_MAPPING = os.sep.join((os.path.curdir, "tests", "data", "nexus-store",
                                     "file-to-resource-mapping.hjson"))


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


@pytest.fixture
def metadata_data_compacted():
    return {
        "_deprecated": False,
        "_updatedBy": "http://integration.kfgorge.test",
        "_rev": 1
    }


@pytest.fixture
def store_metadata_value(metadata_data_compacted):
    data = {"id": "placeholder"}
    data.update(metadata_data_compacted)
    return data


@pytest.fixture
def registered_building(building, model_context, store_metadata_value):
    building.context = model_context.iri if model_context.is_http_iri() else model_context.document[
        "@context"]
    if model_context.base:
        building.id = f"{model_context.base}{str(uuid4())}"
    else:
        building.id = f"{urljoin('file:', pathname2url(os.getcwd()))}/{str(uuid4())}"
    store_metadata_value["id"] = building.id
    building._store_metadata = wrap_dict(store_metadata_value)
    return building


@pytest.fixture
def registered_person(person, store_metadata_value):
    custom_context = person.context
    if custom_context.base:
        person.id = f"{person.base}{str(uuid4())}"
    else:
        person.id = f"{urljoin('file:', pathname2url(os.getcwd()))}/{str(uuid4())}"
    store_metadata_value["id"] = person.id
    person._store_metadata = wrap_dict(store_metadata_value)
    return person


@pytest.fixture
@mock.patch('nexussdk.projects.fetch', return_value=NEXUS_PROJECT_CONTEXT)
@mock.patch('nexussdk.resources.fetch', side_effect=nexussdk.HTTPError('404'))
def nexus_store(context_project_patch, metadata_context_patch):
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token=TOKEN,
                          file_resource_mapping=FILE_RESOURCE_MAPPING)


@pytest.fixture
def nexus_store_unauthorized():
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token="invalid token")


def test_config_error():
    with pytest.raises(ValueError):
        BlueBrainNexus(endpoint="test", bucket="invalid", token="")


def test_config(nexus_store):
    assert nexus_store.organisation == "test"
    assert nexus_store.project == "kgforge"
    assert nexus_store.endpoint == NEXUS
    assert nexus_store.context.base == NEXUS_PROJECT_CONTEXT["base"]


def test_freeze_fail(nexus_store: Store, nested_resource):
    """nested resource is not registered, thus freeze will fail"""
    nexus_store.versioned_id_template = "{x.id}?rev={x._store_metadata._rev}"
    nested_resource.id = "abc"
    add_metadata(nested_resource)


def test_freeze_nested(nexus_store: Store, nested_registered_resource):
    nexus_store.versioned_id_template = "{x.id}?rev={x._store_metadata._rev}"
    nexus_store.freeze(nested_registered_resource)
    do_recursive(assert_frozen_id, nested_registered_resource)


def test_to_resource(nexus_store, registered_building, building_jsonld):
    context = _merge_jsonld(registered_building.context, NEXUS_CONTEXT)
    payload = building_jsonld(registered_building, "compacted", True, None)
    payload["@context"] = context
    result = nexus_store.service.to_resource(payload)
    assert str(result) == str(registered_building)
    assert getattr(result, "context") == registered_building.context
    assert str(result._store_metadata) == str(registered_building._store_metadata)


class TestQuerying:

    @pytest.fixture
    def context(self):
        document = {
            "@context": {
                "contribution": {
                    "@id": "https://neuroshapes.org/contribution",
                    "@type": "@id"
                },
                "agent": {
                    "@id": "http://www.w3.org/ns/prov#agent",
                    "@type": "@id"
                },
                "Person": "http://schema.org/Person",
                "address": "http://schema.org/address",
                "name": "http://schema.org/name",
                "postalCode": "http://schema.org/postalCode",
                "streetAddress": "http://schema.org/streetAddress",
                "deprecated": "https://bluebrain.github.io/nexus/vocabulary/deprecated"
            }
        }
        return Context(document)

    @pytest.mark.parametrize("filters,expected", [
        pytest.param((Filter(["agent", "name"], "__eq__", "Allen Institute"),),
                     (["agent/name ?v0"], ["FILTER(?v0 = \"Allen Institute\")"]),
                     id="literal"),
        pytest.param((Filter(["address", "postalCode"], "__lt__", 50070),),
                     (["address/postalCode ?v0"], ["FILTER(?v0 < 50070)"]),
                     id="number-lt"),
        pytest.param((Filter(["address", "postalCode"], "__gt__", 50070),),
                     (["address/postalCode ?v0"], ["FILTER(?v0 > 50070)"]),
                     id="number-gt"),
        pytest.param((Filter(["address", "postalCode"], "__ge__", 50070),),
                     (["address/postalCode ?v0"], ["FILTER(?v0 >= 50070)"]),
                     id="number-ge"),
        pytest.param((Filter(["address", "postalCode"], "__le__", 50070),),
                     (["address/postalCode ?v0"], ["FILTER(?v0 <= 50070)"]),
                     id="number-le"),
        pytest.param((Filter(["deprecated"], "__eq__", False),),
                     (["deprecated ?v0"], ["FILTER(?v0 = false)"]),
                     id="boolean-false"),
        pytest.param((Filter(["deprecated"], "__eq__", True),),
                     (["deprecated ?v0"], ["FILTER(?v0 = true)"]),
                     id="boolean-true"),
        pytest.param((Filter(["type"], "__eq__", "Person"),),
                     (["type Person"], []),
                     id="iri-eq"),
        pytest.param((Filter(["type"], "__ne__", "Person"),),
                     (["type ?v0"], ["FILTER(?v0 != Person)"]),
                     id="iri-ne"),
        pytest.param((Filter(["type"], "__eq__", "https://github.com/BlueBrain/nexus-forge"),),
                     (["type <https://github.com/BlueBrain/nexus-forge>"], []),
                     id="filter-by-url"),
        pytest.param((Filter(["type"], "__ne__", "Person"), Filter(["name"], "__eq__", "toto")),
                     (["type ?v0", "name ?v1"],
                      ["FILTER(?v0 != Person)", "FILTER(?v1 = \"toto\")"]),
                     id="iri-ne-name-eq")
    ])
    def test_filter_to_query_statements(self, context, filters, expected):
        statements = build_query_statements(context, filters)
        assert statements == expected


# Helpers


def assert_frozen_id(resource: Resource):
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
