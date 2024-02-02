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

from typing import Any
import pytest

from utils import full_path_relative_to_root
from kgforge.specializations.models.rdf_model import RdfModel
from kgforge.specializations.stores.sparql_store import SPARQLStore
from kgforge.core.commons.exceptions import NotSupportedError

SEARCH_ENDPOINT = {"sparql": {"endpoint": "http://dbpedia.org/sparql"}}


@pytest.fixture
def rdf_model():
    model = RdfModel(
        origin='directory',
         source=full_path_relative_to_root("tests/data/dbpedia-model"),
         context={
             'iri': full_path_relative_to_root("tests/data/dbpedia-model/context.json")
         }
    )
    return model


def test_config_(rdf_model):
    with pytest.raises(ValueError):
        SPARQLStore(
            model=rdf_model,
            searchendpoints={"elastic": {"endpoint": "http://demoiri"}}
        )


@pytest.fixture
def sparql_store(rdf_model):
    return SPARQLStore(
        model=rdf_model,
        searchendpoints=SEARCH_ENDPOINT
    )


def test_config(sparql_store, rdf_model):
    assert sparql_store.model == rdf_model
    assert not sparql_store.endpoint
    assert sparql_store.model.context() == rdf_model.context()


def test_search_params(sparql_store):
    with pytest.raises(AttributeError):
        sparql_store.search(resolvers=[None], filters=[None])


def test_elastic_not_supported(sparql_store: Any):
    with pytest.raises(NotSupportedError):
        sparql_store.elastic(query=None, debug=False)
