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