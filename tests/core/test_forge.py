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

# Test suite for initializing a forge.

import pytest

from kgforge.core import KnowledgeGraphForge

SCOPE = "terms"
MODEL = "DemoModel"
STORE = "DemoStore"
RESOLVER = "DemoResolver"


@pytest.fixture(params=[
    MODEL,
    f"{MODEL} from kgforge.specializations.models",
    f"{MODEL} from kgforge.specializations.models.demo_model"])
def model(request):
    return request.param


@pytest.fixture(params=[
    STORE,
    f"{STORE} from kgforge.specializations.stores",
    f"{STORE} from kgforge.specializations.stores.demo_store"])
def store(request):
    return request.param


@pytest.fixture(params=[
    RESOLVER,
    f"{RESOLVER} from kgforge.specializations.resolvers",
    f"{RESOLVER} from kgforge.specializations.resolvers.demo_resolver"])
def resolver(request):
    return request.param


@pytest.fixture
def config(model, store, resolver):
    return {
        "Model": {
            "name": model,
            "origin": "directory",
            "source": "tests/data/demo-model/",
        },
        "Store": {
            "name": store,
        },
        "Resolvers": {
            SCOPE: [
                {
                    "resolver": resolver,
                    "origin": "directory",
                    "source": "tests/data/demo-resolver/",
                    "targets": [
                        {
                            "identifier": "sex",
                            "bucket": "sex.json",
                        },
                    ],
                    "result_resource_mapping": "../../configurations/demo-resolver/term-to-resource-mapping.hjson",
                },
            ],
        },
    }


class TestForgeInitialization:

    def test_initialization(self, config):
        forge = KnowledgeGraphForge(config)
        assert type(forge._model).__name__ == MODEL
        assert type(forge._store).__name__ == STORE
        assert type(forge._resolvers[SCOPE][RESOLVER]).__name__ == RESOLVER
