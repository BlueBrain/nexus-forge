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
import json
import os
from pathlib import Path
from pyshacl import Shape
import pytest
import rdflib

from kgforge.core.resource import Resource
from kgforge.core.commons.exceptions import ValidationError
from kgforge.specializations.models import RdfModel
from kgforge.specializations.models.rdf.directory_service import DirectoryService
from tests.specializations.models.data import *
from utils import full_path_relative_to_root


@pytest.fixture
def shacl_schemas_path():
    return full_path_relative_to_root("tests/data/shacl-model/commons")


@pytest.fixture
def rdf_model(context_iri_file, shacl_schemas_path):
    return RdfModel(
        shacl_schemas_path, context={"iri": context_iri_file}, origin="directory"
    )


class TestVocabulary:

    def test_generate_context(self, rdf_model: RdfModel):
        generated_context = rdf_model._generate_context()
        for k in TYPES_SHAPES_MAP.keys():
            assert generated_context.expand(k) is not None

    def test_types(self, rdf_model: RdfModel):
        types = rdf_model.types(pretty=False)
        assert types == list(TYPES_SHAPES_MAP.keys())

    def test_context(self, rdf_model: RdfModel, context_file_path):
        with open(context_file_path) as f:
            expected = json.load(f)
        vocabulary = rdf_model.context().document
        assert vocabulary == expected

    def test_namespaces(self, rdf_model: RdfModel, model_prefixes):
        assert rdf_model.prefixes(pretty=False) == model_prefixes


class TestTemplates:

    def test_request_invalid_type(self, rdf_model: RdfModel):
        with pytest.raises(ValueError):
            rdf_model._template("Invalid", False)

    @pytest.mark.parametrize(
        "type_, expected",
        [
            pytest.param("Person", PERSON_TEMPLATE, id="person"),
            pytest.param("Employee", EMPLOYEE_TEMPLATE, id="employee"),
            pytest.param("Activity", ACTIVITY_TEMPLATE, id="activity"),
            pytest.param("Building", BUILDING_TEMPLATE, id="building"),
        ],
    )
    def test_create_templates(self, rdf_model: RdfModel, type_, expected):
        result = rdf_model._template(type_, False)
        assert result == expected

    @pytest.mark.parametrize(
        "type_, expected",
        [
            pytest.param("Activity", ACTIVITY_TEMPLATE_MANDATORY, id="activity"),
            pytest.param("Building", BUILDING_TEMPLATE_MANDATORY, id="building"),
        ],
    )
    def test_create_templates_only_required(self, rdf_model: RdfModel, type_, expected):
        result = rdf_model._template(type_, True)
        assert result == expected


class TestValidation:

    @pytest.fixture
    def entity_resource(self):
        return Resource(type="Entity")

    @pytest.fixture
    def activity_json(self, entity_resource):
        return {"type": "Activity", "generated": entity_resource, "status": "completed"}

    @pytest.fixture
    def invalid_activity_resource(self, activity_json):
        return Resource(**activity_json)

    @pytest.fixture
    def valid_activity_resource(self, activity_json):
        resource = Resource(**activity_json)
        resource.id = "http://testing/123"
        return resource

    @pytest.mark.parametrize("type_,", TYPES_SHAPES_MAP.keys())
    def test_type_to_schema(self, rdf_model: RdfModel, type_):
        assert rdf_model.schema_id(type_) == TYPES_SHAPES_MAP[type_]["schema"]

    def test_validate_one(self, rdf_model: RdfModel, valid_activity_resource):
        rdf_model.validate(valid_activity_resource, False, type_="Activity")

    def test_validate_one_fail(self, rdf_model: RdfModel, invalid_activity_resource):
        with pytest.raises(ValidationError):
            rdf_model._validate_one(invalid_activity_resource, type_="Activity")

    def test_validate_with_schema(self, rdf_model: RdfModel, valid_activity_resource):
        rdf_model.validate(valid_activity_resource, False, type_="Activity")

    def test_validate_many(
        self, rdf_model: RdfModel, valid_activity_resource, invalid_activity_resource
    ):
        resources = [valid_activity_resource, invalid_activity_resource]
        rdf_model.validate(resources, False, type_="Activity")
        assert valid_activity_resource._validated is True
        assert invalid_activity_resource._validated is False
        assert (
            valid_activity_resource._last_action.operation
            == invalid_activity_resource._last_action.operation
            == rdf_model._validate_many.__name__
        )

    def test_get_shape_graph(self, rdf_model: RdfModel, shacl_schemas_path):
        assert isinstance(rdf_model.service, DirectoryService)
        assert isinstance(rdf_model.service._graph, rdflib.Dataset)
        shape_graphs = [str(g.identifier) for g in rdf_model.service._graph.graphs()]
        assert len(shape_graphs) == 4
        assert sorted(shape_graphs) == sorted(
            [
                str(f.resolve())
                for f in Path(shacl_schemas_path).rglob(os.path.join("*.*"))
            ]
            + ["urn:x-rdflib:default"]
        )
        expected_targeted_classes = list(TYPES_SHAPES_MAP.keys())

        loaded_classes = [
            rdf_model.service.context.to_symbol(cls)
            for cls in rdf_model.service.class_to_shape.keys()
        ]
        assert sorted(loaded_classes) == sorted(expected_targeted_classes)
        expected_shapes = [val["shape"] for val in TYPES_SHAPES_MAP.values()]
        loaded_shapes = [str(s) for s in rdf_model.service.shape_to_named_graph.keys()]
        assert sorted(loaded_shapes) == sorted(expected_shapes)
        for s in TYPES_SHAPES_MAP.values():
            shape, schema_graph = rdf_model.service.get_shape_graph(
                rdflib.term.URIRef(s["shape"])
            )
            assert isinstance(shape, Shape)
            assert str(shape.node) == s["shape"]
            assert isinstance(schema_graph, rdflib.Graph)
            assert len(schema_graph) > 0
