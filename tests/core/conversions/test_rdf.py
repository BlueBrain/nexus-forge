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

# Placeholder for the test suite for conversion of a resource to / from triples.
import os
from urllib.parse import urljoin
from urllib.request import pathname2url

import json
import pytest
from rdflib import Graph, BNode

from kgforge.core.commons.exceptions import NotSupportedError
from kgforge.core.conversions.rdf import _merge_jsonld, from_jsonld, as_jsonld, Form, as_graph

form_store_metadata_combinations = [
    pytest.param(Form.COMPACTED.value, True, id="compacted-with-metadata"),
    pytest.param(Form.COMPACTED.value, False, id="compacted-without-metadata"),
    pytest.param(Form.EXPANDED.value, True, id="expanded-with-metadata"),
    pytest.param(Form.EXPANDED.value, False, id="expanded-without-metadata")
]

store_metadata_params = [
    pytest.param(True, id="with-metadata"),
    pytest.param(False, id="without-metadata")
]


@pytest.fixture
def building_with_context(building, model_context):
    building.context = model_context.document["@context"]
    return building


class TestJsonLd:

    @pytest.mark.parametrize("store_metadata", store_metadata_params)
    def test_nested_resources(self, organization, organization_jsonld_compacted,
                              store_metadata, model_context, metadata_context):
        compacted = organization_jsonld_compacted(organization, store_metadata=store_metadata)
        result = as_jsonld(organization, form=Form.COMPACTED.value, store_metadata=store_metadata,
                           model_context=model_context, metadata_context=metadata_context,
                           context_resolver=None)
        assert compacted == result

    @pytest.mark.parametrize("form, store_metadata", form_store_metadata_combinations)
    def test_no_context(self, form, store_metadata, valid_resource):
        with pytest.raises(NotSupportedError):
            as_jsonld(valid_resource, form=form, store_metadata=store_metadata, model_context=None,
                      metadata_context=None, context_resolver=None)

    @pytest.mark.parametrize("form, store_metadata", form_store_metadata_combinations)
    def test_unregistered_resource_with_context(self, building_with_context, building_jsonld,
                                                form, store_metadata, metadata_context):
        expected = building_jsonld(building_with_context, form, store_metadata, None)

        result = as_jsonld(building_with_context, form=form, store_metadata=store_metadata,
                           model_context=None, metadata_context=metadata_context,
                           context_resolver=None)
        assert expected == result

    @pytest.mark.parametrize("form, store_metadata", form_store_metadata_combinations)
    def test_registered_resource_with_context(self, building_with_context, make_registered,
                                              building_jsonld, form, store_metadata,
                                              store_metadata_value, metadata_context):
        base = urljoin('file:', pathname2url(os.getcwd()))
        registered_resource = make_registered(building_with_context, store_metadata_value, base)
        expected = building_jsonld(registered_resource, form, store_metadata, None)
        result = as_jsonld(registered_resource, form=form, store_metadata=store_metadata,
                           model_context=None, metadata_context=metadata_context,
                           context_resolver=None)
        assert expected == result

    @pytest.mark.parametrize("form, store_metadata", form_store_metadata_combinations)
    def test_unregistered_resource_model_context(self, building, model_context, building_jsonld,
                                                 form, store_metadata, metadata_context):
        expected = building_jsonld(building, form, store_metadata, model_context.document["@context"])
        result = as_jsonld(building, form=form, store_metadata=store_metadata,
                           model_context=model_context, metadata_context=metadata_context,
                           context_resolver=None)

        assert expected == result

    @pytest.mark.parametrize("form, store_metadata", form_store_metadata_combinations)
    def test_registered_resource_model_context(self, building_with_context, model_context,
                                               make_registered, building_jsonld, form,
                                               store_metadata, store_metadata_value,
                                               metadata_context):
        base = urljoin('file:', pathname2url(os.getcwd()))
        registered_resource = make_registered(building_with_context, store_metadata_value, base)
        expected = building_jsonld(registered_resource, form, store_metadata, None)
        result = as_jsonld(registered_resource, form=form, store_metadata=store_metadata,
                           model_context=model_context, metadata_context=metadata_context,
                           context_resolver=None)
        assert expected == result

    def test_from_jsonld(self, building, model_context, building_jsonld):
        building.context = model_context.document["@context"]
        payload = building_jsonld(building, "compacted", False, None)
        resource = from_jsonld(payload)
        assert resource == building

    def test_from_jsonld_2(self, building, model_context, building_jsonld):
        payload = {
            "@context": {
                "sh": "http://www.w3.org/ns/shacl#",
                "ex": "http://test/vocab#",
                "parent": {
                    "@id": "ex:parent",
                    "@type": "@id"
                },
                "nodeKind": {
                    "@id": "sh:nodeKind",
                    "@type": "@id"
                },
                "BlankNode": {
                    "@id": "sh:BlankNode"
                },
                "NodeShape": {
                    "@id": "sh:NodeShape"
                },
                "SuperClass": {
                    "@id": "ex:SuperClass"
                }
            },
            "@id": "http://test/data/123",
            "@type": "NodeShape",
            "parent": "ex:SuperClass",
            "nodeKind": "sh:BlankNode"
        }
        resource_dict = from_jsonld(payload)
        print(resource_dict)


        assert True

    def test_unresolvable_context(self, building, building_jsonld):
        building.context = "http://unresolvable.context.example.org/"
        payload = building_jsonld(building, "compacted", False, None)
        with pytest.raises(ValueError):
            from_jsonld(payload)


class TestGraph:

    def test_as_graph(self, building, building_jsonld, model_context):
        store_metadata = False
        building.id = "http://test/1234"
        building.context = model_context .document["@context"]
        data = building_jsonld(building, "compacted", store_metadata, None)
        expected = Graph().parse(data=json.dumps(data), format="json-ld")
        result = as_graph(building, store_metadata, model_context, None, None)
        for s, p, o in expected:
            if isinstance(o, BNode):
                assert (s, p, None) in result
            elif isinstance(s, BNode):
                assert (None, p, o) in result
            else:
                assert (s, p, o) in result


class TestUtils:

    def test_merge_jsonld(self):
        str_ctx = "string_context"
        str_ctx2 = "string_context2"
        dict_ctx = {"a": 1, "b": 2}
        dict_ctx2 = {"c": 3, "d": 4}
        list_ctx = [str_ctx, dict_ctx]
        list_ctx2 = [str_ctx2, dict_ctx2]
        dict_ctx3 = {"a": 1, "b": 2, "c": 3, "d": 4}
        assert _merge_jsonld(str_ctx, str_ctx2) == [str_ctx, str_ctx2]
        assert _merge_jsonld(str_ctx, dict_ctx) == [str_ctx, dict_ctx]
        assert _merge_jsonld(str_ctx2, list_ctx) == [str_ctx2, str_ctx, dict_ctx]
        assert _merge_jsonld(list_ctx, str_ctx2) == [str_ctx, dict_ctx, str_ctx2]
        assert _merge_jsonld(list_ctx, dict_ctx2) == [str_ctx, dict_ctx3]
        assert _merge_jsonld(list_ctx, list_ctx2) == [str_ctx, dict_ctx3, str_ctx2]
        assert _merge_jsonld(dict_ctx, str_ctx) == [dict_ctx, str_ctx]
        assert _merge_jsonld(dict_ctx, list_ctx2) == [dict_ctx3, str_ctx2]
        assert _merge_jsonld(dict_ctx, dict_ctx2) == dict_ctx3
        assert _merge_jsonld(str_ctx, str_ctx) == str_ctx
        assert _merge_jsonld(dict_ctx, dict_ctx) == dict_ctx
        assert _merge_jsonld(list_ctx, list_ctx) == list_ctx
        assert _merge_jsonld(list_ctx, None) == list_ctx
