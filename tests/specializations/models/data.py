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
from copy import deepcopy

from rdflib import URIRef

from tests.conftest import shacl_schemas_file_path


ORGANIZATION = {
    "id": "",
    "type": "Organization",
    "name": "",
    "parentOrganization": {"id": "", "type": "Organization"},
}

PERSON_TEMPLATE = {
    "id": "",
    "type": "Person",
    "address": {"type": "PostalAddress", "postalCode": ["", 0], "streetAddress": ""},
    "birthDate": "9999-12-31",
    "deathDate": "9999-12-31",
    "gender": ["female", "male"],
    "givenName": "",
    "familyName": "",
}

EMPLOYEE_TEMPLATE = deepcopy(PERSON_TEMPLATE)
EMPLOYEE_TEMPLATE["type"] = "Employee"
EMPLOYEE_TEMPLATE.update(
    {
        "colleague": {
            "type": "Person",
            "id": "",
            "address": {
                "type": "PostalAddress",
                "postalCode": ["", 0],
                "streetAddress": "",
            },
            "birthDate": "9999-12-31",
            "deathDate": "9999-12-31",
            "gender": ["female", "male"],
            "givenName": "",
            "familyName": "",
        },
        "contractor": {
            "id": "",
            "type": "Organization",
            "name": "",
            "parentOrganization": {"id": "", "type": "Organization"},
        },
        "department": {
            "id": "",
            "type": "Organization",
            "name": "",
            "parentOrganization": {"id": "", "type": "Organization"},
        },
        "startDate": "9999-12-31",
        "worksFor": {"id": "", "type": ["Organization", "Person"]},
    }
)
employee_keys_order = [
    "id",
    "type",
    "address",
    "birthDate",
    "colleague",
    "contractor",
    "deathDate",
    "department",
    "gender",
    "givenName",
    "familyName",
    "startDate",
    "worksFor",
]
EMPLOYEE_TEMPLATE = {k: EMPLOYEE_TEMPLATE[k] for k in employee_keys_order}

ENTITY = {"id": "", "type": "Entity"}

ACTIVITY_TEMPLATE = {
    "id": "",
    "type": "Activity",
    "citation": {"id": ""},
    "endedAtTime": "9999-12-31T00:00:00",
    "generated": ENTITY,
    "startedAtTime": "9999-12-31T00:00:00",
    "status": "completed",
    "used": ENTITY,
    "validated": False,
    "author": {"id": "", "type": ["Organization", "Person"]},
}

ACTIVITY_TEMPLATE_MANDATORY = {
    k: v
    for k, v in ACTIVITY_TEMPLATE.items()
    if k in ["id", "type", "generated", "status"]
}

BUILDING_TEMPLATE = {
    "id": "",
    "type": "Building",
    "description": "",
    "geo": {"latitude": 0.0, "longitude": 0.0},
    "image": {"id": ""},
    "name": "",
}
BUILDING_TEMPLATE_MANDATORY = {
    k: v
    for k, v in BUILDING_TEMPLATE.items()
    if k in ["id", "type", "description", "name"]
}

TYPES_SHAPES_MAP = {
    "Activity": {
        "shape": "http://www.example.com/ActivityShape",
        "schema": "http://shapes.ex/activity",
        "named_graph": f"{shacl_schemas_file_path}/shapes-2.json",
        "imports":  {"schema":[], "ontology":[]},
        "parent_node_shapes": [],
        "number_of_direct_property_shapes": 9,
        "number_of_inherited_property_shapes": 0,
    },
    "Association": {
        "shape": "http://www.example.com/AssociationShape",
        "schema": "http://shapes.ex/person",
        "named_graph": f"{shacl_schemas_file_path}/shapes-1.json",
        "imports":  {"schema":[], "ontology":[]},
        "parent_node_shapes": [],
        "number_of_direct_property_shapes": 1,
        "number_of_inherited_property_shapes": 0,
    },
    "Building": {
        "shape": "http://www.example.com/BuildingShape",
        "schema": "http://shapes.ex/building",
        "named_graph": f"{shacl_schemas_file_path}/shapes-3.json",
        "imports":  {"schema":[], "ontology":[]},
        "parent_node_shapes": [],
        "number_of_direct_property_shapes": 4,
        "number_of_inherited_property_shapes": 0,
    },
    "Employee": {
        "shape": "http://www.example.com/EmployeeShape",
        "schema": "http://shapes.ex/employee",
        "named_graph": f"{shacl_schemas_file_path}/shapes-4.json",
        "imports":  {"schema":["http://shapes.ex/person"], "ontology":["https://schema.org/"]},
        "parent_node_shapes": [URIRef("http://www.example.com/PersonShape")],
        "number_of_direct_property_shapes": 0,
        "number_of_inherited_property_shapes": 6,
    },
    "Organization": {
        "shape": "http://www.example.com/OrganizationShape",
        "schema": "http://shapes.ex/person",
        "named_graph": f"{shacl_schemas_file_path}/shapes-1.json",
        "imports": {"schema":[], "ontology":[]},
        "parent_node_shapes": [],
        "number_of_direct_property_shapes": 2,
        "number_of_inherited_property_shapes": 0,
    },
    "Person": {
        "shape": "http://www.example.com/PersonShape",
        "schema": "http://shapes.ex/person",
        "named_graph": f"{shacl_schemas_file_path}/shapes-1.json",
        "imports": {"schema":[], "ontology":["https://schema.org/"]},
        "parent_node_shapes": [],
        "number_of_direct_property_shapes": 6,
        "number_of_inherited_property_shapes": 0,
    },
    "PostalAddress": {
        "shape": "https://schema.org/PostalAddress",
        "schema": "http://shapes.ex/person",
        "named_graph": f"{shacl_schemas_file_path}/shapes-1.json",
        "imports":  {"schema":[], "ontology":[]},
        "parent_node_shapes": [],
        "number_of_direct_property_shapes": 2,
        "number_of_inherited_property_shapes": 0,
    },
}
