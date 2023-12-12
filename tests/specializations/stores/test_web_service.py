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
from kgforge.specializations.stores.web_service_store import WebServiceStore

ENDPOINT = "http://neuromorpho.org/api/neuron"


@pytest.fixture
def rdf_model():
    model = RdfModel(
        origin='directory',
         source=full_path_relative_to_root("examples/mappings/NeuroMorpho"),
         context={
             'iri': full_path_relative_to_root("examples/mappings/NeuroMorpho/jsonld_context.json")
         }
    )
    return model


#   model: Model,
#         endpoint: str,
#         content_type: str,
#         accept: str,
#         response_location : Optional[str] = None,
#         files_download: Optional[Dict] = None,
#         searchendpoints : Optional[Dict] = None,
#         health_endpoint: Optional[str] = None,

def test_config_searchendpoints(rdf_model: RdfModel):
    with pytest.raises(ValueError):
        WebServiceStore(
            model=rdf_model,
            endpoint=ENDPOINT,
            content_type="application/json",
            accept="*/*",
            searchendpoints={"elastic": None}
        )


@pytest.fixture
def sparql_store(rdf_model: RdfModel):
    return SPARQLStore(
        model=rdf_model,
    )


def test_config(sparql_store: Any, rdf_model: RdfModel):
    assert sparql_store.model == rdf_model
    assert not sparql_store.endpoint
    assert sparql_store.model.context() == rdf_model.context()


def test_search_params(sparql_store: Any):
    with pytest.raises(ValueError):
        sparql_store.search(resolvers=[None], filters=[None])