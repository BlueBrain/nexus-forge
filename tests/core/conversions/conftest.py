#
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

import pytest

from kgforge.core import KnowledgeGraphForge, Resource


@pytest.fixture
def forge():
    config = {
        "Model": {
            "name": "DemoModel",
            "origin": "directory",
            "source": "tests/data/demo-model/",
        },
        "Store": {
            "name": "DemoStore",
        },
    }
    return KnowledgeGraphForge(config)


@pytest.fixture
def r1():
    return Resource(id="123", type="Type", p1="v1a", p2="v2a")


@pytest.fixture
def r2():
    return Resource(id="345", type="Type", p1="v1b", p2="v2b")


@pytest.fixture
def r3(r1):
    return Resource(id="678", type="Other", p3="v3c", p4=r1)


@pytest.fixture
def r4(r2):
    return Resource(id="912", type="Other", p3="v3d", p4=r2)


@pytest.fixture
def r5():
    return Resource(p5="v5e", p6="v6e")
