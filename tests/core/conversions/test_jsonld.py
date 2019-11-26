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

from kgforge.core.conversions.jsonld import as_jsonld
from tests.data import *


@pytest.mark.parametrize("resource, expected", [
    pytest.param(RESOURCE_1, JSON_LD_1, id="standard-json-ld"),
    pytest.param(RESOURCE_2, JSON_LD_2, id="no-context"),
    pytest.param(RESOURCE_3, JSON_LD_3, id="local-context-list-1"),
    pytest.param(RESOURCE_4, JSON_LD_4, id="local-context-list-2"),
])
def test_as_jsonld(resource, expected):
    data = as_jsonld(resource, True, False)
    assert data == expected, "data is not as the expected"
