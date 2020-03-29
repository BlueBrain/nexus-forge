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

from copy import deepcopy

import json
import pytest

from kgforge.specializations.models import RdfModel

PERSON = {
    "id": "",
    "type": "Person",
    "address":
        {
            "type": "PostalAddress",
            "postalCode": "",
            "streetAddress": "",
        },
    "birthDate": "9999-12-31",
    "deathDate": "9999-12-31",
    "gender": ["female", "male"],
    "givenName": "",
    "name": ""
}

EMPLOYEE = deepcopy(PERSON)
EMPLOYEE["type"] = "Employee"
EMPLOYEE.update({
    "colleague": "Person",
    "contractor": "Organization",
    "department": "Organization",
    "startDate": "9999-12-31",
    "worksFor": [
        {"type": "Organization"},
        {"type": "Person"}
    ]
})
employee_keys_order = ["id", "type", "address", "birthDate", "colleague", "contractor", "deathDate",
                       "department", "gender", "givenName", "name", "startDate", "worksFor"]
EMPLOYEE = {k: EMPLOYEE[k] for k in employee_keys_order}

ACTIVITY = {
    "id": "",
    "type": "Activity",
    "citation": "",
    "endedAtTime": "9999-12-31T00:00:00",
    "generated": "Entity",
    "startedAtTime": "9999-12-31T00:00:00",
    "status": "completed",
    "used": "Entity",
    "validated": False,
    "wasStartedBy": "Person"
}

ACTIVITY_MANDATORY = {k: v for k, v in ACTIVITY.items() if k in ["id", "type", "generated", "status"]}


BUILDING = {
    "id": "",
    "type": "Building",
    "description": "",
    "geo": {
        "latitude": 0.0,
        "longitude": 0.0
    },
    "image": "",
    "name": ""
}
BUILDING_MANDATORY = {k: v for k, v in BUILDING.items() if k in ["id", "type", "description", "name"]}

TYPES_SCHEMAS_MAP = {
    "Activity": "http://www.example.com/ActivityShape",
    "Association": "http://www.example.com/AssociationShape",
    "Building": "http://www.example.com/BuildingShape",
    "Employee": "http://www.example.com/EmployeeShape",
    "Person": "http://www.example.com/PersonShape",
    "PostalAddress": "http://schema.org/PostalAddress",
}


@pytest.fixture()
def namespaces_dict():
    return {
        'xml': 'http://www.w3.org/XML/1998/namespace',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'prov': 'http://www.w3.org/ns/prov#',
        'schema': 'http://schema.org/',
        'dash': 'http://datashapes.org/dash#',
        'ex': 'http://example.org/',
        'sh': 'http://www.w3.org/ns/shacl#',
        'shapes': 'http://www.example.com/',
        'this': 'http://www.example.com/'
    }


@pytest.fixture()
def shacl_model(context_iri_file):
    return RdfModel("tests/data/shacl-model",
                    context={"iri": context_iri_file},
                    origin="directory")


class TestVocabulary:

    def test_types(self, shacl_model: RdfModel):
        types = shacl_model.types(pretty=False)
        assert types == list(TYPES_SCHEMAS_MAP.keys())

    def test_context(self, shacl_model: RdfModel, context_file_path):
        with open(context_file_path) as f:
            expected = json.load(f)
        vocabulary = shacl_model.context().document
        assert vocabulary == expected

    def test_namespaces(self, shacl_model: RdfModel, namespaces_dict):
        assert shacl_model.prefixes(pretty=False) == namespaces_dict


class TestTemplates:

    def test_request_invalid_type(self, shacl_model: RdfModel):
        with pytest.raises(ValueError):
            shacl_model._template("Invalid", False)

    @pytest.mark.parametrize("type_, expected", [
        pytest.param("Person", PERSON, id="person"),
        pytest.param("Employee", EMPLOYEE, id="employee"),
        pytest.param("Activity", ACTIVITY, id="activity"),
        pytest.param("Building", BUILDING, id="building"),
    ])
    def test_create_templates(self, shacl_model: RdfModel, type_, expected):
        result = shacl_model._template(type_, False)
        assert result == expected

    @pytest.mark.parametrize("type_, expected", [
        pytest.param("Activity", ACTIVITY_MANDATORY, id="activity"),
        pytest.param("Building", BUILDING_MANDATORY, id="building"),
    ])
    def test_create_templates_only_required(self, shacl_model: RdfModel, type_, expected):
        result = shacl_model._template(type_, True)
        assert result == expected


class TestValidation:

    @pytest.mark.parametrize("type_,", TYPES_SCHEMAS_MAP.keys())
    def test_schema_id(self, shacl_model: RdfModel, type_):
        assert shacl_model.schema_id(type_) == TYPES_SCHEMAS_MAP[type_]
