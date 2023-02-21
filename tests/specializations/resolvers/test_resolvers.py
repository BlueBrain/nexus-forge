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
import re
import pytest

from kgforge.specializations.resolvers.ontology_resolver import _write_resolving_query
from kgforge.core.archetypes.resolver import write_sparql_filters

@pytest.fixture
def text():
    return "L6_BC"

@pytest.fixture
def limit():
    return 3

@pytest.fixture
def first_filters():
    filters = f"?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> \"false\"^^xsd:boolean"
    return filters

@pytest.fixture
def filter_properties():
    return ['label', 'notation', 'prefLabel', 'altLabel']

@pytest.fixture
def property_filters(text, filter_properties):
    return write_sparql_filters(text, filter_properties, False, False)


ontolgy_contexts = [{"name": "celltypes",
          "property": "nsg:defines",
          "position": "subject",
          "value": "http://bbp.epfl.ch/neurosciencegraph/ontologies/core/celltypes"},
         {"name": "brainregions",
          "property": "nsg:defines",
          "position": "subject",
          "value": "http://bbp.epfl.ch/neurosciencegraph/ontologies/core/brainregion"}]

filled_standard_query = """\nCONSTRUCT {
  ?id a ?type .
  ?id label ?label .
  ?id prefLabel ?prefLabel .
  ?id altLabel ?altLabel .
  ?id definition ?definition .
  ?id subClassOf ?subClassOf .
  ?id isDefinedBy ?isDefinedBy .
  ?id notation ?notation .
} WHERE {
  ?id a ?type .
  ?id label ?label . 
  OPTIONAL { ?id prefLabel ?prefLabel . }
  OPTIONAL { ?id altLabel ?altLabel . }
  OPTIONAL { ?id definition ?definition . }
  OPTIONAL { ?id subClassOf ?subClassOf . }
  OPTIONAL { ?id isDefinedBy ?isDefinedBy . }     
  OPTIONAL { ?id notation ?notation . }    
  {
    SELECT * WHERE {
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; label ?label  FILTER (?label = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; notation ?notation  FILTER (?notation = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; prefLabel ?prefLabel  FILTER (?prefLabel = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; altLabel ?altLabel  FILTER (?altLabel = "L6_BC") } 
    } LIMIT 3
  }
}
"""

filled_celltypes_query = """\nCONSTRUCT {
  ?id a ?type .
  ?id label ?label .
  ?id prefLabel ?prefLabel .
  ?id altLabel ?altLabel .
  ?id definition ?definition .
  ?id subClassOf ?subClassOf .
  ?id isDefinedBy ?isDefinedBy .
  ?id notation ?notation .
} WHERE {
  ?id a ?type .
  ?id label ?label . 
  OPTIONAL { ?id prefLabel ?prefLabel . }
  OPTIONAL { ?id altLabel ?altLabel . }
  OPTIONAL { ?id definition ?definition . }
  OPTIONAL { ?id subClassOf ?subClassOf . }
  OPTIONAL { ?id isDefinedBy ?isDefinedBy . }     
  OPTIONAL { ?id notation ?notation . }    
  <http://bbp.epfl.ch/neurosciencegraph/ontologies/core/celltypes> nsg:defines ?id .
  {
    SELECT * WHERE {
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; label ?label  FILTER (?label = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; notation ?notation  FILTER (?notation = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; prefLabel ?prefLabel  FILTER (?prefLabel = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; altLabel ?altLabel  FILTER (?altLabel = "L6_BC") } 
    } LIMIT 3
  }
}
"""

filled_brainregion_query = """\nCONSTRUCT {
  ?id a ?type .
  ?id label ?label .
  ?id prefLabel ?prefLabel .
  ?id altLabel ?altLabel .
  ?id definition ?definition .
  ?id subClassOf ?subClassOf .
  ?id isDefinedBy ?isDefinedBy .
  ?id notation ?notation .
} WHERE {
  ?id a ?type .
  ?id label ?label . 
  OPTIONAL { ?id prefLabel ?prefLabel . }
  OPTIONAL { ?id altLabel ?altLabel . }
  OPTIONAL { ?id definition ?definition . }
  OPTIONAL { ?id subClassOf ?subClassOf . }
  OPTIONAL { ?id isDefinedBy ?isDefinedBy . }     
  OPTIONAL { ?id notation ?notation . }    
  <http://bbp.epfl.ch/neurosciencegraph/ontologies/core/brainregion> nsg:defines ?id .
  {
    SELECT * WHERE {
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; label ?label  FILTER (?label = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; notation ?notation  FILTER (?notation = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; prefLabel ?prefLabel  FILTER (?prefLabel = "L6_BC") } UNION
      { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; altLabel ?altLabel  FILTER (?altLabel = "L6_BC") } 
    } LIMIT 3
  }
}
"""

@pytest.mark.parametrize(
    "contexts, resolving_context, expected",
    [
    pytest.param((None), (None),
                (filled_standard_query),
                id="standard query",),
    pytest.param((ontolgy_contexts), ("celltypes"),
                 (filled_celltypes_query),
                 id="cell types query",),
    pytest.param((ontolgy_contexts), ("brainregions"),
                 (filled_brainregion_query),
                 id="brain regions query",),
    ],
    )
def test_write_query(contexts, resolving_context, expected, first_filters, filter_properties,
                     property_filters, limit):
    expected_fields = ["type", "label"]
    optional_fields = ["prefLabel", "altLabel", "definition", "subClassOf", "isDefinedBy", "notation"]
    constructed_query = _write_resolving_query(first_filters, filter_properties, property_filters,
                           expected_fields, optional_fields, contexts,
                           resolving_context, limit)
    filled = re.sub('\\s+',' ', expected) 
    new = re.sub('\\s+',' ', constructed_query) 
    assert new == filled