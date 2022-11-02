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

from kgforge.core import Resource, KnowledgeGraphForge
from kgforge.core.commons.context import Context
from kgforge.core.wrappings.paths import Filter
from kgforge.specializations.databases.store_database import StoreDatabase
from kgforge.specializations.databases.utils import type_from_filters
from kgforge.core.commons.exceptions import ConfigurationError
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


@pytest.fixture
def model_config():
    return {
        "name": "DemoModel",
        "origin": "directory",
        "source": "tests/data/demo-model/"
    }

@pytest.fixture
def db_config():
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

@pytest.fixture
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


def test_database_config(forge, db_config, model_config):
    with pytest.raises(ValueError):
        StoreDatabase(db_config) # Missing forge
    with pytest.raises(ValueError):
        StoreDatabase(forge, **db_config) # Missing name
    with pytest.raises(ValueError):
        # Missing model
        StoreDatabase(forge, **{'name': 'mydb', 'origin': 'store',
                       'source':'tests/data/demo-store/'})
    with pytest.raises(ConfigurationError):
        StoreDatabase(forge, **{'name': 'mydb', 'origin': 'store',
                       'source':'tests/data/demo-store/',
                       'model': model_config})

def test_database_directory(forge, model_config):
    with pytest.raises(Exception):
        StoreDatabase(forge, **{'name': 'mydb', 'origin': 'directory',
                       'source':'tests/data/demo-store/',
                       'model': model_config})

def test_database_web_serice(forge, model_config):
    with pytest.raises(Exception):
        StoreDatabase(forge, **{'name': 'mydb', 'origin': 'web_service',
                       'source':'tests/data/demo-store/',
                       'model': model_config})

