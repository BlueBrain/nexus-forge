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


def _build_type_to_shapemap_item(
    shape,
    schema,
    named_graph,
    imports,
    indirect_imports,
    parent_node_shapes,
    number_of_direct_property_shapes,
    number_of_inherited_property_shapes,
):
    return {
        "shape": shape,
        "schema": schema,
        "named_graph": named_graph,
        "imports": imports,
        "indirect_imports": indirect_imports,
        "parent_node_shapes": parent_node_shapes,
        "number_of_direct_property_shapes": number_of_direct_property_shapes,
        "number_of_inherited_property_shapes": number_of_inherited_property_shapes,
    }


TYPES_SHAPES_MAP = {
    "Activity": _build_type_to_shapemap_item(
        "http://www.example.com/ActivityShape",
        "http://shapes.ex/activity",
        f"{shacl_schemas_file_path}/shapes-2.json",
        {"schema": [], "ontology": []},
        {"schema": [], "ontology": []},
        [],
        9,
        0,
    ),
    "Association": _build_type_to_shapemap_item(
        "http://www.example.com/AssociationShape",
        "http://shapes.ex/person",
        f"{shacl_schemas_file_path}/shapes-1.json",
        {"schema": [], "ontology": ["https://schema.org/"]},
        {"schema": [], "ontology": []},
        [],
        1,
        0,
    ),
    "Building": _build_type_to_shapemap_item(
        "http://www.example.com/BuildingShape",
        "http://shapes.ex/building",
        f"{shacl_schemas_file_path}/shapes-3.json",
        {"schema": [], "ontology": []},
        {"schema": [], "ontology": []},
        [],
        4,
        0,
    ),
    "Employee": _build_type_to_shapemap_item(
        "http://www.example.com/EmployeeShape",
        "http://shapes.ex/employee",
        f"{shacl_schemas_file_path}/shapes-4.json",
        {"schema": ["http://shapes.ex/person"], "ontology": []},
        {"schema": [], "ontology": ["https://schema.org/"]},
        [URIRef("http://www.example.com/PersonShape")],
        0,
        6,
    ),
    "Organization": _build_type_to_shapemap_item(
        "http://www.example.com/OrganizationShape",
        "http://shapes.ex/person",
        f"{shacl_schemas_file_path}/shapes-1.json",
        {"schema": [], "ontology": ["https://schema.org/"]},
        {"schema": [], "ontology": []},
        [],
        2,
        0,
    ),
    "PostalAddress": _build_type_to_shapemap_item(
        "https://schema.org/PostalAddress",
        "http://shapes.ex/person",
        f"{shacl_schemas_file_path}/shapes-1.json",
        {"schema": [], "ontology": ["https://schema.org/"]},
        {"schema": [], "ontology": []},
        [],
        2,
        0,
    ),
    "Person": _build_type_to_shapemap_item(
        "http://www.example.com/PersonShape",
        "http://shapes.ex/person",
        f"{shacl_schemas_file_path}/shapes-1.json",
        {"schema": [], "ontology": ["https://schema.org/"]},
        {"schema": [], "ontology": []},
        [],
        6,
        0,
    ),
}
