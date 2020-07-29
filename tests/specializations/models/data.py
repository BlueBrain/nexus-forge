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


ORGANIZATION = {
    "id": "",
    "type": "Organization",
    "name": "",
    "parentOrganization": {
        "id": "",
        "type": "Organization"
    }
}

PERSON_TEMPLATE = {
    "id": "",
    "type": "Person",
    "address":
        {
            "type": "PostalAddress",
            "postalCode": ["",0],
            "streetAddress": "",
        },
    "birthDate": "9999-12-31",
    "deathDate": "9999-12-31",
    "gender": ["female", "male"],
    "givenName": "",
    "familyName":""
}

EMPLOYEE_TEMPLATE = deepcopy(PERSON_TEMPLATE)
EMPLOYEE_TEMPLATE["type"] = "Employee"
EMPLOYEE_TEMPLATE.update({
    "colleague": {
        "type": "Person",
        "id": "",
        "address":
        {
            "type": "PostalAddress",
            "postalCode": ["",0],
            "streetAddress": "",
        },
        "birthDate": "9999-12-31",
        "deathDate": "9999-12-31",
        "gender": ["female", "male"],
        "givenName": "",
        "familyName":""
    },
    "contractor": {
        "id": "",
        "type": "Organization",
        "name": "",
        "parentOrganization": {
            "id": "",
            "type": "Organization"
        }
    },
    "department": {
        "id": "",
        "type": "Organization",
        "name": "",
        "parentOrganization": {
            "id": "",
            "type": "Organization"
        }
    },
    "startDate": "9999-12-31",
    "worksFor": {
        "id": "",
        "type": ["Organization", "Person"]
    }
})
employee_keys_order = ["id", "type", "address", "birthDate", "colleague", "contractor", "deathDate",
                       "department", "gender", "givenName", "familyName", "startDate", "worksFor"]
EMPLOYEE_TEMPLATE = {k: EMPLOYEE_TEMPLATE[k] for k in employee_keys_order}

ENTITY =  {
    "id": "",
    "type": "Entity"
}

ACTIVITY_TEMPLATE = {
    "id": "",
    "type": "Activity",
    "citation": {
        "id": ""
    },
    "endedAtTime": "9999-12-31T00:00:00",
    "generated": ENTITY,
    "startedAtTime": "9999-12-31T00:00:00",
    "status": "completed",
    "used": ENTITY,
    "validated": False,
    "author": {
        "id": "",
        "type": ["Organization", "Person"]
    }
}

ACTIVITY_TEMPLATE_MANDATORY = {k: v for k, v in ACTIVITY_TEMPLATE.items() if k in ["id", "type", "generated", "status"]}

BUILDING_TEMPLATE = {
    "id": "",
    "type": "Building",
    "description": "",
    "geo": {
        "latitude": 0.0,
        "longitude": 0.0
    },
    "image": {
        "id": ""
    },
    "name": ""
}
BUILDING_TEMPLATE_MANDATORY = {k: v for k, v in BUILDING_TEMPLATE.items() if k in ["id", "type", "description", "name"]}

TYPES_SCHEMAS_MAP = {
    "Activity": "http://www.example.com/ActivityShape",
    "Association": "http://www.example.com/AssociationShape",
    "Building": "http://www.example.com/BuildingShape",
    "Employee": "http://www.example.com/EmployeeShape",
    "Organization": "http://www.example.com/OrganizationShape",
    "Person": "http://www.example.com/PersonShape",
    "PostalAddress": "http://schema.org/PostalAddress",
}