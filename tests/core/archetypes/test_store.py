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

# Placeholder for the test suite for actions.
import pytest

from kgforge.core.archetypes.store import rewrite_sparql


context = {
    "@context": {
        "type": {
            "@id": "rdf:type",
            "@type": "@id"
        },
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "prov": "http://www.w3.org/ns/prov#",
        "schema": "http://schema.org/",
        "Person": {
            "@id": "schema:Person",
            "@type": "@id"
        },
        "Association": "prov:Association",
        "name": "schema:name",
        "agent": "prov:agent",
        "description": "http://schema.org/description",
    }
}


prefixes = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "http://schema.org/",
}


prefixes_string = "\n".join([f"PREFIX {k}: <{v}>" for k, v in prefixes.items()])


form_store_metadata_combinations = [
    ("SELECT ?agent WHERE { <http://exaplpe.org/1234> agent ?agent }",
     prefixes_string + "\nSELECT ?agent WHERE { <http://exaplpe.org/1234> prov:agent ?agent }"),
    ("SELECT ?agent WHERE { ?agent type ?v0 FILTER(?v0 != Person) }",
     prefixes_string + "\nSELECT ?agent WHERE { ?agent rdf:type ?v0 FILTER(?v0 != schema:Person) }"),
    ("SELECT ?x ?name WHERE { ?x type Association ; agent/name ?name }",
     prefixes_string + "\nSELECT ?x ?name WHERE { ?x rdf:type prov:Association ; prov:agent/schema:name ?name }"),
    ("SELECT ?name WHERE { ?x agent/name ?name FILTER regex(?name, \"^j\", \"i\") }",
     prefixes_string + "\nSELECT ?name WHERE { ?x prov:agent/schema:name ?name FILTER regex(?name, \"^j\", \"i\") }"),
    ("SELECT ?x WHERE { <http://exaplpe.org/1234> description ?x }",
     prefixes_string + "\nSELECT ?x WHERE { <http://exaplpe.org/1234> <http://schema.org/description> ?x }"),
]


@pytest.mark.parametrize("query, expected", form_store_metadata_combinations)
def test_rewrite_sparql(query, expected):
    result = rewrite_sparql(query, context, prefixes)
    assert result == expected