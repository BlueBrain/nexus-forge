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

from kgforge.core import Resource

"""
All examples only consider we json-ld COMPACTED
TODO: implement transformations for other RDF formats
"""
CONTEXT_1 = {
    "name": "http://schema.org/name",
    "description": "http://schema.org/description",
    "image": "http://schema.org/image",
    "Building": "http://schema.org/Building",
    "geo": "http://schema.org/geo",
    "latitude": {
        "@id": "http://schema.org/latitude",
        "@type": "xsd:float"
    },
    "longitude": {
        "@id": "http://schema.org/longitude",
        "@type": "xsd:float"
    },
    "xsd": "http://www.w3.org/2001/XMLSchema#"
}
IDENTIFIER_1 = "http://example.org/7244eb28-98b9-4b38-8b1e-a456f2c070f9"
JSON_LD_1 = {
    "@context": CONTEXT_1,
    "@id": "http://example.org/7244eb28-98b9-4b38-8b1e-a456f2c070f9",
    "@type": "Building",
    "description": "The Empire State Building is a 102-story landmark in New York City.",
    "geo": {
        "latitude": "40.75",
        "longitude": "73.98"
    },
    "image": "http://www.civil.usherbrooke.ca/cours/gci215a/empire-state-building.jpg",
    "name": "The Empire State Building"
}
RESOURCE_1 = Resource(id="http://example.org/7244eb28-98b9-4b38-8b1e-a456f2c070f9", type="Building",
                      name="The Empire State Building",
                      description="The Empire State Building is a 102-story landmark in New York City.",
                      image="http://www.civil.usherbrooke.ca/cours/gci215a/empire-state-building.jpg",
                      geo=Resource(**{"latitude": "40.75", "longitude": "73.98"}))
RESOURCE_1._context = CONTEXT_1

ingredient = [
    "12 fresh mint leaves",
    "1/2 lime, juiced with pulp",
    "1 tablespoons white sugar",
    "1 cup ice cubes",
    "2 fluid ounces white rum",
    "1/2 cup club soda"
]
instructions = [
    {
        "description": "Crush lime juice, mint and sugar together in glass.",
        "step": 1
    },
    {
        "description": "Fill glass to top with ice cubes.",
        "step": 2
    },
    {
        "description": "Pour white rum over ice.",
        "step": 3
    },
    {
        "description": "Fill the rest of glass with club soda, stir.",
        "step": 4
    },
    {
        "description": "Garnish with a lime wedge.",
        "step": 5
    }
]
IDENTIFIER_2 = "http://example.org/mojito"
JSON_LD_2 = {
    "@id": "http://example.org/mojito",
    "ingredient": ingredient,
    "instructions": instructions,
    "name": "Mojito"
}
RESOURCE_2 = Resource(id="http://example.org/mojito", name="Mojito", ingredient=ingredient,
                      instructions=[Resource(**i) for i in instructions])


CONTEXT_3 = {
    "@base": "http://example.org/",
    "@vocab": "http://schema.org/"
}
JSON_LD_3 = {
    "@context": CONTEXT_3,
    "@id": "person1",
    "@type": "Person",
    "employer": {
        "@id": "ep",
        "@type": "Organisation",
        "label": "Ecole Politechique"
    },
    "name": "Elia Nicols"
}
IDENTIFIER_3 = "http://example.org/person1"
employer = Resource(id="http://example.org/ep", label="Ecole Politechique", type="Organisation")
employer._context = CONTEXT_3
RESOURCE_3 = Resource(id="http://example.org/person1", type="Person", name="Elia Nicols", employer=employer)
RESOURCE_3._context = CONTEXT_3

CONTEXT_4 = CONTEXT_3
JSON_LD_4 = {
    "@context": CONTEXT_4,
    "@type": "Publication",
    "contributor": [
        {
            "@type": "Person",
            "name": "First Author"
        },
        {
            "@type": "Person",
            "name": "Second Author"
        },
        {
            "@type": "Person",
            "name": "Third Author"
        }
    ],
    "title": "The state of the art"
}
RESOURCE_4 = Resource(type="Publication", title="The state of the art",
                      contributor=[
                          Resource(type="Person", name="First Author"),
                          Resource(type="Person", name="Second Author"),
                          Resource(type="Person", name="Third Author")])
RESOURCE_4._context = CONTEXT_4


CONTEXT_5 = [
    {
        "@base": "https://data.org/",
        "@vocab": "https://vocab.org/",
    },
    'https://bluebrain.github.io/nexus/contexts/resource.json'
]
JSON_LD_5 = {
    "@context": CONTEXT_5,
    "@id": "b684ed06-9404-4f3e-8b11-f5ebded1dbbd",
    "@type": "Publication",
    "author": {
        "@type": "Person",
        "name": "First Author"
    },
    "title": "My publication",
    "_self": "https://nexus/v1/resources/bbp_test/kgforge/_/b684ed06-9404-4f3e-8b11-f5ebded1dbbd",
    "_constrainedBy": "https://bluebrain.github.io/nexus/schemas/unconstrained.json",
    "_project": "https://nexus/v1/projects/bbp_test/kgforge",
    "_rev": 1,
    "_deprecated": False,
    "_createdAt": "2019-10-21T06:30:16.239846Z",
    "_createdBy": "https://nexus/v1/realms/bbp/users/annonymous",
    "_updatedAt": "2019-10-21T06:30:16.239846Z",
    "_updatedBy": "https://nexus/v1/realms/bbp/users/annonymous",
    "_incoming": "https://nexus/v1/resources/bbp_test/kgforge/_/b684ed06-9404-4f3e-8b11-f5ebded1dbbd/incoming",
    "_outgoing": "https://nexus/v1/resources/bbp_test/kgforge/_/b684ed06-9404-4f3e-8b11-f5ebded1dbbd/outgoing"
}
RESOURCE_5 = Resource(id="https://data.org/b684ed06-9404-4f3e-8b11-f5ebded1dbbd", type="Publication",
                      title="My publication", author=Resource(type="Person", name="First Author"))
RESOURCE_5._context = {
    "@base": "https://data.org/",
    "@vocab": "https://vocab.org/",
}
RESOURCE_5._store_metadata = {
    "_self": "https://nexus/v1/resources/bbp_test/kgforge/_/b684ed06-9404-4f3e-8b11-f5ebded1dbbd",
    "_constrainedBy": "https://bluebrain.github.io/nexus/schemas/unconstrained.json",
    "_project": "https://nexus/v1/projects/bbp_test/kgforge",
    "_rev": 1,
    "_deprecated": False,
    "_createdAt": "2019-10-21T06:30:16.239846Z",
    "_createdBy": "https://nexus/v1/realms/bbp/users/annonymous",
    "_updatedAt": "2019-10-21T06:30:16.239846Z",
    "_updatedBy": "https://nexus/v1/realms/bbp/users/annonymous",
    "_incoming": "https://nexus/v1/resources/bbp_test/kgforge/_/b684ed06-9404-4f3e-8b11-f5ebded1dbbd/incoming",
    "_outgoing": "https://nexus/v1/resources/bbp_test/kgforge/_/b684ed06-9404-4f3e-8b11-f5ebded1dbbd/outgoing"
}
