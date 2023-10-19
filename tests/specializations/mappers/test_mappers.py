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

# Placeholder for the generic parameterizable test suite for mappers.

import pytest
from contextlib import nullcontext as does_not_raise

from kgforge.core import KnowledgeGraphForge, Resource
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping


@pytest.fixture
def mapping_str():
    return """
    {
        type: x.type
        id: x.id
        content_type: {
            unitCode: f"bytes"
            value: x.p1
        }
        encodingFormat: x.p2
    }
    """


@pytest.mark.parametrize(
    "json_to_map, exception",
    [
        ({"id": "123", "type": "Type", "p1": "v1a", "p2": "v2a"}, does_not_raise()),
        ({"id": "123", "p1": "v1a", "p2": "v2a"}, pytest.raises(AttributeError)),

    ],
)
def test_mapping_load_no_mapping_type(
        exception, config, json_to_map, mapping_str
):

    forge = KnowledgeGraphForge(config)

    mapping = DictionaryMapping.load(mapping_str)

    with exception:
        DictionaryMapper(forge).map(json_to_map, mapping, None)


