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

from utils import full_path_relative_to_root
from kgforge.specializations.models.rdf_model import RdfModel
from kgforge.specializations.stores.sparql_store import SPARQLStore


SEARCH_ENDPOINT = {"sparql": {"endpoint": "http://dbpedia.org/sparql"}}


@pytest.fixture
def rdfmodel():
    model = RdfModel(origin='directory',
                     source=full_path_relative_to_root("tests/data/dbpedia-model"),
                     context={'iri': full_path_relative_to_root("tests/data/dbpedia-model/context.json")}
                     )
    return model

def test_config_(rdfmodel):
    with pytest.raises(ValueError):
        SPARQLStore(
            model=rdfmodel,
            searchendpoints={"elastic": {"endpoint": "http://demoiri"}}
        )

@pytest.fixture
def sparqlstore(rdfmodel):
    return SPARQLStore(
        model=rdfmodel,
        searchendpoints=SEARCH_ENDPOINT
    )

def test_config(sparqlstore, rdfmodel):
    assert sparqlstore.model == rdfmodel
    assert not sparqlstore.endpoint
    assert sparqlstore.model.context() == rdfmodel.context()

def test_search_params(sparqlstore):
    with pytest.raises(ValueError):
        sparqlstore.search(resolvers=[None], filters=[None])
