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

import hjson
import pytest
from rdflib.term import URIRef

from kgforge.specializations.models import ShaclModel

PERSON_PROPS = {
    "id": "",
    "type": "Person",
    "address":
        {
            "type": "Address",
            "postalCode": "",
            "streetAddress": "",
        },
    "birthDate": "9999-12-31",
    "deathDate": "9999-12-31",
    "gender": ["female", "male"],
    "givenName": "",
    "name": ""
}

PERSON = deepcopy(PERSON_PROPS)

employee_tmp = deepcopy(PERSON_PROPS)
employee_tmp["type"] = "Employee"
employee_tmp["contractor"] = "Organization"
employee_tmp["department"] = "Organization"
employee_tmp["startDate"] = "9999-12-31"
employee_tmp["supervisor"] = "Employee"
employee_tmp["founder"] = [
    {"type": "Organization"},
    {"type": "Person"}
]
employee_keys_order = ["id", "type", "address", "birthDate", "contractor", "deathDate",
                       "department", "founder", "gender", "givenName", "name", "startDate",
                       "supervisor"]
EMPLOYEE = {k: employee_tmp[k] for k in employee_keys_order}

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

ACTIVITY_MANDATORY = {
    "id": "",
    "type": "Activity",
    "generated": "Entity",
    "status": "completed"
}

BUILDING = {
    "id": "",
    "type": "Building",
    "description": "",
    "geo": {
        "latitude": 0.0,
        "longitude": 0.0
    },
    "name": ""
}

BUILDING_MANDATORY = {
    "id": "",
    "type": "Building",
    "description": "",
    "name": ""
}


@pytest.fixture(scope="session")
def shacl_model():
    return ShaclModel("tests/data/shacl-model/")


def test_get_types(shacl_model: ShaclModel):
    types = shacl_model.types()
    all_types = ("Person", "Address", "Employee", "Activity", "Building")
    assert set(types) == set(all_types)
    assert shacl_model.service.types_shapes_map["Activity"] == URIRef("http://www.example.com/ActivityShape")
    assert shacl_model.service.types_shapes_map["Building"] == URIRef("http://www.example.com/BuildingShape")
    assert shacl_model.service.types_shapes_map["Person"] == URIRef("http://www.example.com/PersonShape")
    assert shacl_model.service.types_shapes_map["Address"] == URIRef("http://schema.org/Address")
    assert shacl_model.service.types_shapes_map["Employee"] == URIRef("http://www.example.com/EmployeeShape")


def test_request_invalid_type(shacl_model: ShaclModel):
    with pytest.raises(ValueError):
        shacl_model.template("Invalid", False)


@pytest.mark.parametrize("type_, expected", [
    pytest.param("Person", PERSON, id="person"),
    pytest.param("Employee", EMPLOYEE, id="employee"),
    pytest.param("Activity", ACTIVITY, id="activity"),
    pytest.param("Building", BUILDING, id="building"),
])
def test_create_templates(shacl_model: ShaclModel, type_, expected):
    template = hjson.dumps(expected, indent=4)
    result = shacl_model.template(type_, False)
    assert result == template


@pytest.mark.parametrize("type_, expected", [
    pytest.param("Activity", ACTIVITY_MANDATORY, id="activity"),
    pytest.param("Building", BUILDING_MANDATORY, id="building"),
])
def test_create_templates_only_required(shacl_model: ShaclModel, type_, expected):
    template = hjson.dumps(expected, indent=4)
    result = shacl_model.template(type_, True)
    assert result == template
