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
import pytest
from rdflib import RDFS

from kgforge.core.resource import Resource
from kgforge.core.commons.exceptions import ValidationError
from kgforge.specializations.models import RdfModel
from tests.specializations.models.data import *


class TestVocabulary:

    def test_generate_context(self, rdf_model_from_dir: RdfModel):
        generated_context = rdf_model_from_dir._generate_context()
        for k in TYPES_SHAPES_MAP.keys():
            assert generated_context.expand(k) is not None

    def test_types(self, rdf_model_from_dir: RdfModel):
        types = rdf_model_from_dir.types(pretty=False)
        assert sorted(types) == sorted(list(TYPES_SHAPES_MAP.keys()))

    def test_context(self, rdf_model_from_dir: RdfModel, context_file_path):
        with open(context_file_path) as f:
            expected = json.load(f)
        vocabulary = rdf_model_from_dir.context().document
        assert vocabulary == expected

    def test_namespaces(self, rdf_model_from_dir: RdfModel, model_prefixes):
        assert rdf_model_from_dir.prefixes(pretty=False) == model_prefixes


class TestTemplates:

    def test_request_invalid_type(self, rdf_model_from_dir: RdfModel):
        with pytest.raises(ValueError):
            rdf_model_from_dir._template("Invalid", False)

    @pytest.mark.parametrize(
        "type_, expected",
        [
            pytest.param("Person", PERSON_TEMPLATE, id="person"),
            pytest.param("Employee", EMPLOYEE_TEMPLATE, id="employee"),
            pytest.param("Activity", ACTIVITY_TEMPLATE, id="activity"),
            pytest.param("Building", BUILDING_TEMPLATE, id="building"),
        ],
    )
    def test_create_templates(self, rdf_model_from_dir: RdfModel, type_, expected):
        result = rdf_model_from_dir._template(type_, False)
        assert result == expected

    @pytest.mark.parametrize(
        "type_, expected",
        [
            pytest.param("Activity", ACTIVITY_TEMPLATE_MANDATORY, id="activity"),
            pytest.param("Building", BUILDING_TEMPLATE_MANDATORY, id="building"),
        ],
    )
    def test_create_templates_only_required(
        self, rdf_model_from_dir: RdfModel, type_, expected
    ):
        result = rdf_model_from_dir._template(type_, True)
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

    @pytest.fixture
    def valid_patient_resource(self, activity_json):
        resource = Resource(
            type="Patient",
            familyName="Doe",
            givenName="John",
            gender="male",
            birthDate="2004-04-12T13:20:15.5",
        )
        resource.id = "https://testing/1234"
        return resource

    @pytest.mark.parametrize("type_,", TYPES_SHAPES_MAP.keys())
    def test_type_to_schema(self, rdf_model_from_dir: RdfModel, type_):
        assert rdf_model_from_dir.schema_id(type_) == TYPES_SHAPES_MAP[type_]["schema"]

    def test_validate_one(self, rdf_model_from_dir: RdfModel, valid_activity_resource):
        rdf_model_from_dir.validate(
            valid_activity_resource, False, type_="Activity", inference=None
        )
        assert valid_activity_resource._last_action.succeeded == True
        assert valid_activity_resource._validated == True

    def test_validate_one_fail(
        self, rdf_model_from_dir: RdfModel, invalid_activity_resource
    ):
        with pytest.raises(ValidationError):
            rdf_model_from_dir._validate_one(
                invalid_activity_resource, type_="Activity", inference=None
            )

    @pytest.mark.parametrize(
        "inference, type, succeeded, validated",
        [
            pytest.param("rdfs", "Person", True, True, id="rdfs_person"),
            pytest.param("none", "Person", False, False, id="none_str_person"),
            pytest.param(None, "Person", False, False, id="none_person"),
        ],
    )
    def test_validate_with_ontology(
        self,
        rdf_model_from_dir: RdfModel,
        valid_patient_resource,
        inference,
        type,
        succeeded,
        validated,
    ):
        assert len(rdf_model_from_dir.service._imported) == 0
        assert valid_patient_resource.get_type() == "Patient"
        assert (
            URIRef("https://schema.org/Patient"),
            RDFS.subClassOf,
            URIRef(f"https://schema.org/{type}"),
        ) in rdf_model_from_dir.service._dataset_graph
        rdf_model_from_dir.validate(
            valid_patient_resource, False, type_=type, inference=inference
        )
        assert valid_patient_resource._last_action.succeeded == succeeded
        assert valid_patient_resource._validated == validated

    def test_validate_many(
        self,
        rdf_model_from_dir: RdfModel,
        valid_activity_resource,
        invalid_activity_resource,
    ):
        resources = [valid_activity_resource, invalid_activity_resource]
        rdf_model_from_dir.validate(resources, False, type_="Activity")
        assert valid_activity_resource._validated is True
        assert invalid_activity_resource._validated is False
        assert (
            valid_activity_resource._last_action.operation
            == invalid_activity_resource._last_action.operation
            == rdf_model_from_dir._validate_many.__name__
        )
