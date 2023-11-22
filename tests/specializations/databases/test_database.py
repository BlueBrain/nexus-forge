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
import copy
import pytest

from kgforge.core import Resource, KnowledgeGraphForge
from kgforge.core.commons.context import Context
from kgforge.core.wrappings.paths import Filter
from kgforge.specializations.databases import WebServiceDatabase
from kgforge.specializations.databases.store_database import StoreDatabase
from kgforge.specializations.databases.utils import type_from_filters
from kgforge.core.commons.exceptions import ConfigurationError, QueryingError
from kgforge.core.wrappings.dict import DictWrapper, wrap_dict
import json

from tests.specializations.stores.test_sparql import dict_context


@pytest.mark.parametrize(
    "filters,expected",
    [
        pytest.param(
            ({'type': 'Person'}),
            ('Person'),
            id="dictionary_type",
        ),
        pytest.param(
            ({'id': 'my_id'}),
            (None),
            id="dictionary_notype",
        ),
        pytest.param(
            (Filter(['id'], '__eq__', 'some_id')),
            (None),
            id="one_filter_notype",
        ),
        pytest.param(
            (Filter(['type'], '__eq__', 'Person')),
            ('Person'),
            id="one_filter_type",
        ),
        pytest.param(
            (Filter(['id'], '__eq__', 'some_id'),
            Filter(['label'], '__eq__', 'some_label')),
            None,
            id="two_filters_notype",
        ),
        pytest.param(
            (Filter(['id'], '__eq__', 'some_id'),
             Filter(['type'], '__eq__', 'Person')),
            'Person',
            id="two_filters_type",
        ),
        pytest.param(
            (Filter(['type'], '__eq__', 'Protein'),
             Filter(['type'], '__eq__', 'Person')),
            'Protein',
            id="two_filters_two_types",
        ),
    ]
)
def test_type_from_filters(filters, expected):
    assert type_from_filters(filters) == expected


@pytest.fixture
def context(dict_context):
    return Context(dict_context)


def forge(db_config, model_config):
    config = {
        "Model": model_config,
        "Store": {
            "name": "DemoStore",
        },
        "Databases": {
            'dbpedia': db_config
        }
    }
    return KnowledgeGraphForge(config)

@pytest.fixture
def model_config():
    return {
        "name": "DemoModel",
        "origin": "directory",
        "source": "tests/data/demo-model/"
    }

@pytest.fixture
def storedb_config():
    return {
            "origin": "store",
            "source": "SPARQLStore",
            "searchendpoints":{
                "sparql":{
                    "endpoint": "http://dbpedia.org/sparql"
                },

            },
            "model": {
                    "name": "DemoModel",
                    "origin": "directory",
                    "source": "tests/data/demo-model/",
                    "context":{
                        "iri": "test/data/dbpedia"
                    }
            }
    }
class TestStoreDB:

    @pytest.fixture
    def forge_with_store(self, storedb_config, model_config):
        return forge(storedb_config, model_config)

    def test_database_config(self, forge_with_store, storedb_config, model_config):
        with pytest.raises(ValueError):
            StoreDatabase(storedb_config) # Missing forge
        with pytest.raises(ValueError):
            StoreDatabase(forge_with_store, **storedb_config) # Missing name
        with pytest.raises(ValueError):
            # Missing model
            StoreDatabase(forge_with_store, **{'name': 'mydb', 'origin': 'store',
                           'source':'tests/data/demo-store/'})
        with pytest.raises(ConfigurationError):
            StoreDatabase(forge_with_store, **{'name': 'mydb', 'origin': 'store',
                           'source':'tests/data/demo-store/',
                           'model': model_config})

    def test_database_directory(self, forge_with_store, model_config):
        with pytest.raises(Exception):
            StoreDatabase(forge_with_store, **{'name': 'mydb', 'origin': 'directory',
                           'source':'tests/data/demo-store/',
                           'model': model_config})

    def test_database_wrong_web_service(self, forge_with_store, model_config):
        with pytest.raises(Exception):
            StoreDatabase(forge_with_store, **{'name': 'mydb', 'origin': 'web_service',
                           'source':'tests/data/demo-store/',
                           'model': model_config})


@pytest.fixture
def ws_db_config():
    return {
            "name": "uniprot",
            "origin": "web_service",
            "source": "https://rest.uniprot.org/uniprotkb/",
            "model": {
                    "name": "DemoModel",
                    "origin": "directory",
                    "source": "tests/data/demo-model/",
                    "context":{
                        "iri": "examples/database-sources/UniProt"
                    }
            },
            "max_connection": 10,
            "content_type": "application/json;charset=UTF-8",
            "accept": "*/*"
    }

class TestWebServiceDB:
    @pytest.fixture
    def forge_with_wsdb(self, ws_db_config, model_config):
        return forge(ws_db_config, model_config)

    def test_database_config(self, forge_with_wsdb, ws_db_config, model_config):
        with pytest.raises(ValueError):
            WebServiceDatabase(ws_db_config) # Missing forge
        with pytest.raises(ValueError):
            # Missing model
            WebServiceDatabase(forge_with_wsdb, **{'name': 'mydb', 'origin': 'web_service',
                           'source':'tests/data/demo-store/', 'max_connection': 5,
                           'content_type': 'application/json', 'accept': '*/*'})
        with pytest.raises(ValueError):
            # Missing max_connection
            WebServiceDatabase(forge_with_wsdb, **{'name': 'mydb', 'origin': 'web_service',
                           'source':'tests/data/demo-store/',
                           'content_type': 'application/json', 'accept': '*/*'})
        with pytest.raises(ValueError):
            # Missing content_type
            WebServiceDatabase(forge_with_wsdb, **{'name': 'mydb', 'origin': 'web_service',
                           'source':'tests/data/demo-store/', 'max_connection': 5,
                           'content_type': 'application/json'})
        
    def test_database_directory(self, forge_with_wsdb, model_config):
        with pytest.raises(Exception):
            WebServiceDatabase(forge_with_wsdb, **{'name':'mydb', 'origin': 'directory',
                           'source':'tests/data/demo-store/',
                           'model': model_config})
    def test_database_wrong_store(self, forge_with_wsdb, model_config):
        with pytest.raises(Exception):
            WebServiceDatabase(forge_with_wsdb, **{'name': 'mydb', 'origin': 'store',
                           'source':'tests/data/demo-store/',
                           'model': model_config})

    def test_searchendpoint_config(self, forge_with_wsdb, ws_db_config):
        tmp_config = copy.deepcopy(ws_db_config)
        tmp_config['searchendpoints'] = {'some_endpoint': {'wrong': 'True'}}
        with pytest.raises(ConfigurationError):
            WebServiceDatabase(forge_with_wsdb, **tmp_config)

    def test_search(self, forge_with_wsdb, ws_db_config):
        tmp_config = copy.deepcopy(ws_db_config)
        tmp_config['searchendpoints'] = {'some_endpoint': {'endpoint': "https://my_endpoint.com/API/"}}
        db = WebServiceDatabase(forge_with_wsdb, **tmp_config)
        with pytest.raises(ConfigurationError):
            db.search([], {'type': 'Protein'}, searchendpoint='uniprot')
        with pytest.raises(QueryingError):
            db.search([], {'type': 'Protein'})