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
from kgforge.core.commons.exceptions import ConfigurationError, NotSupportedError
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


def test_config_searchendpoints(rdf_model: RdfModel):
    with pytest.raises(ConfigurationError):
        WebServiceStore(
            model=rdf_model,
            endpoint=ENDPOINT,
            request_params={
                "content_type":"application/json",
                "accept":"*/*"},
            searchendpoints={"elastic": None}
        )


def test_config_file_downloads_content_type(rdf_model: RdfModel):
    with pytest.raises(ConfigurationError):
        WebServiceStore(
            model=rdf_model,
            endpoint=ENDPOINT,
            request_params={
                "content_type":"application/json",
                "accept":"*/*",
                "files_download": {"Accept": "application/json"}},
            )


def test_config_file_downloads_accept(rdf_model: RdfModel):
    with pytest.raises(ConfigurationError):
        WebServiceStore(
            model=rdf_model,
            endpoint=ENDPOINT,
            request_params={
                "content_type":"application/json",
                "accept":"*/*",
                "files_download": {"Content-Type": "application/json"}},
            )


@pytest.fixture
def web_service_store(rdf_model: RdfModel):
    return WebServiceStore(
        model=rdf_model,
        endpoint=ENDPOINT,
        request_params={
                "content_type":"application/json",
                "accept":"*/*",
                "files_download": {"Content-Type": "application/json",
                                 "Accept": "*/*"}
        },
        health_endpoint="https://mynotreal.com/health"
    )


def test_config(web_service_store: Any, rdf_model: RdfModel):
    assert web_service_store.model == rdf_model
    assert web_service_store.service.endpoint
    assert web_service_store.model.context() == rdf_model.context()


def test_health_not_valid(web_service_store):
    with pytest.raises(ConfigurationError):
        web_service_store.health()


def test_sparql_not_implemented(web_service_store: Any):
    with pytest.raises(NotSupportedError):
        web_service_store.sparql(query="SELECT * WHERE { ?s ?p ?o }")


def test_elastic_not_supported(web_service_store: Any):
    with pytest.raises(NotSupportedError):
        web_service_store.elastic(query=None, debug=False)


def test_retrieve_not_supported(web_service_store: Any):
    with pytest.raises(NotSupportedError):
        web_service_store.retrieve(id=None, version=None, cross_bucket=False)
