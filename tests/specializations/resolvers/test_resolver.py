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

# Placeholder for the generic parameterizable test suite for resolvers.
from kgforge.core.archetypes.resolver import _build_resolving_query
from kgforge.core.commons.sparql_query_builder import SPARQLQueryBuilder
import pytest

from kgforge.core.commons.strategies import ResolvingStrategy

@pytest.mark.parametrize(
        "filters, query_template, properties_to_filter_with, text, expected_query",
        [
            pytest.param(
                {"path_1":"value_1"},
                ("""
        CONSTRUCT {{
            ?id a ?type ;
            label ?label ;
            prefLabel ?prefLabel ;
            altLabel ?altLabel ;
            definition ?definition;
            subClassOf ?subClassOf ;
            isDefinedBy ?isDefinedBy ;
            notation ?notation
        }} WHERE {{
            ?id a ?type ;
                label ?label ; 
            OPTIONAL {{
            ?id subClassOf ?subClassOf ;
            }}
            OPTIONAL {{
            ?id definition ?definition ;
            }}
            OPTIONAL {{
            ?id prefLabel ?prefLabel .
            }}
            OPTIONAL {{
            ?id altLabel ?altLabel .
            }}
            OPTIONAL {{
            ?id isDefinedBy ?isDefinedBy .
            }}     
            OPTIONAL {{
            ?id notation ?notation .
            }}    
            {{
            SELECT * WHERE {{
                {{ {0} ; label ?label {1} }} UNION
                {{ {0} ; notation ?notation {2} }} UNION
                {{ {0} ; prefLabel ?prefLabel {3} }} UNION
                {{ {0} ; altLabel ?altLabel {4} }}
            }} LIMIT {5}
            }}
        }}
        """),
        (['label', 'notation', 'prefLabel', 'altLabel']),
        ('L6_BC'),
                (
                    
                """
        CONSTRUCT {
            ?id a ?type ;
            label ?label ;
            prefLabel ?prefLabel ;
            altLabel ?altLabel ;
            definition ?definition;
            subClassOf ?subClassOf ;
            isDefinedBy ?isDefinedBy ;
            notation ?notation
        } WHERE {
            ?id a ?type ;
                label ?label ; 
            OPTIONAL {
            ?id subClassOf ?subClassOf ;
            }
            OPTIONAL {
            ?id definition ?definition ;
            }
            OPTIONAL {
            ?id prefLabel ?prefLabel .
            }
            OPTIONAL {
            ?id altLabel ?altLabel .
            }
            OPTIONAL {
            ?id isDefinedBy ?isDefinedBy .
            }     
            OPTIONAL {
            ?id notation ?notation .
            }    
            {
            SELECT * WHERE {
                { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a Class ; 
 path_1 ?v0 . 
 FILTER(?v0 = "value_1") ; label ?label  FILTER (?label = "L6_BC") } UNION
                { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a Class ; 
 path_1 ?v0 . 
 FILTER(?v0 = "value_1") ; notation ?notation  FILTER (?notation = "L6_BC") } UNION
                { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a Class ; 
 path_1 ?v0 . 
 FILTER(?v0 = "value_1") ; prefLabel ?prefLabel  FILTER (?prefLabel = "L6_BC") } UNION
                { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a Class ; 
 path_1 ?v0 . 
 FILTER(?v0 = "value_1") ; altLabel ?altLabel  FILTER (?altLabel = "L6_BC") }
            } LIMIT 1
            }
        }
        """
                ),
                id="ontology_query_str"
            ),
            pytest.param(
                {"path_1":"value_1"},
                (
                """
            CONSTRUCT {{
                ?id a ?type ;
                name ?name ;
                givenName ?givenName ;
                familyName ?familyName
            }} WHERE {{
              ?id a ?type . 
              OPTIONAL {{
                ?id name ?name .
              }}
              OPTIONAL {{
                ?id givenName ?givenName . 
              }}
              OPTIONAL {{
                ?id familyName ?familyName .
              }}
              {{
                SELECT * WHERE {{
                  {{ {0} ; name ?name {1} }} UNION
                  {{ {0} ; familyName ?familyName; givenName ?givenName {2} }} UNION
                  {{ {0} ; familyName ?familyName; givenName ?givenName {3} }}
                }} LIMIT {4}
              }}
            }}
            """),
            (['name', 'givenName', 'familyName']),
            ("EPFL"),
                ("""
            CONSTRUCT {
                ?id a ?type ;
                name ?name ;
                givenName ?givenName ;
                familyName ?familyName
            } WHERE {
              ?id a ?type . 
              OPTIONAL {
                ?id name ?name .
              }
              OPTIONAL {
                ?id givenName ?givenName . 
              }
              OPTIONAL {
                ?id familyName ?familyName .
              }
              {
                SELECT * WHERE {
                  { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a Class ; 
 path_1 ?v0 . 
 FILTER(?v0 = "value_1") ; name ?name  FILTER (?name = "EPFL") } UNION
                  { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a Class ; 
 path_1 ?v0 . 
 FILTER(?v0 = "value_1") ; familyName ?familyName; givenName ?givenName  FILTER (?givenName = "EPFL") } UNION
                  { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a Class ; 
 path_1 ?v0 . 
 FILTER(?v0 = "value_1") ; familyName ?familyName; givenName ?givenName  FILTER (?familyName = "EPFL") }
                } LIMIT 1
              }
            }
            """),
                id="agent_query_str"
            )
        ]
    )
def test_write_query(bbn_deprecated_property,filters, query_template, properties_to_filter_with, text, expected_query, model_context):
    constructed_query, limit = _build_resolving_query(text, query_template, bbn_deprecated_property, filters, ResolvingStrategy.EXACT_MATCH, "Class", properties_to_filter_with, model_context, SPARQLQueryBuilder, 10)
    assert limit == 1
    assert expected_query == constructed_query
