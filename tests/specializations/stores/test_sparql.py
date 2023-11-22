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

import pytest

from kgforge.core.commons.context import Context
from kgforge.specializations.stores.sparql import SPARQLStore


SEARCH_ENDPOINT = {"sparql": {"endpoint": "http://dbpedia.org/sparql"}}

@pytest.fixture
def dict_context():
    document = {
        "@context": {
        "owl": "http://www.w3.org/2002/07/owl#",
        "owl2xml": "http://www.w3.org/2006/12/owl2-xml#",
        "swrlb": "http://www.w3.org/2003/11/swrlb#",
        "protege": "http://protege.stanford.edu/plugins/owl/protege#",
        "swrl":  "http://www.w3.org/2003/11/swrl#",
        "xsd":   "http://www.w3.org/2001/XMLSchema#",
        "skos":  "http://www.w3.org/2004/02/skos/core#",
        "rdfs":  "http://www.w3.org/2000/01/rdf-schema#",
        "rdf":   "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "foaf":  "http://xmlns.com/foaf/0.1/",
        "dbpedia2": "http://dbpedia.org/property/",
        "dbpedia": "http://dbpedia.org/",
        "dbo":   "http://dbpedia.org/ontology/",
        "dbr": "http://dbpedia.org/resource/",
        "id": {
            "@id": "http://www.geneontology.org/formats/oboInOwl#id"
        },
        "MusicalArtist": {
            "@id": "dbo:MusicalArtist"
        },
        "birthDate": {
            "@id": "dbo:birthDate"
        },
        "birthPlace": {
            "@id": "dbo:birthPlace"
        },
        "type": {
            "@id": "rdf:type"
        },
        "Berlin": {
            "@id": "dbr:Berlin"
        },
        "@id": "https://bbp.epfl.ch/jsonldcontext/db/dbpedia"
    }
    }
    return document

@pytest.fixture
def store_context(dict_context):
    return Context(dict_context)

@pytest.fixture
def sparql_store(store_context):
    return SPARQLStore(
        model_context=store_context,
        searchendpoints=SEARCH_ENDPOINT,
        store_context=store_context
    )

def test_config_error():
    with pytest.raises(ValueError):
        SPARQLStore(endpoint="test", bucket="invalid")

def test_config(sparql_store, store_context):
    assert sparql_store.bucket == None
    assert sparql_store.endpoint == None
    assert sparql_store.context == store_context

def test_search_params(sparql_store):
    with pytest.raises(ValueError):
        sparql_store.search(filters=[None])