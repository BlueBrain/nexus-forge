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

# Placeholder for the generic parameterizable test suite for mappings.


import pytest
from contextlib import nullcontext as does_not_raise

from kgforge.core.archetypes.mapping import MappingType
from kgforge.specializations.mappings import DictionaryMapping
from utils import full_path_relative_to_root

mapping_url_valid = "https://raw.githubusercontent.com/BlueBrain/nexus-forge/master/examples" \
                    "/configurations/nexus-store/file-to-resource-mapping.hjson"

mapping_path_valid = full_path_relative_to_root(
    "tests/data/nexus-store/file-to-resource-mapping.hjson"
)


@pytest.mark.parametrize(
    "source, exception",
    [
        (mapping_path_valid, does_not_raise()),
        (mapping_url_valid, does_not_raise()),
    ],
)
def test_mapping_load_no_mapping_type(source, exception):
    with exception:
        mapping = DictionaryMapping.load(source)


@pytest.mark.parametrize(
    "source, mapping_type, exception",
    [
        (mapping_path_valid, MappingType.FILE, does_not_raise()),
        (mapping_url_valid, MappingType.URL, does_not_raise()),
        ("i", MappingType.URL, pytest.raises(Exception)),
    ],
)
def test_mapping_load_mapping_type(source, mapping_type, exception):
    with exception:
        mapping = DictionaryMapping.load(source, mapping_type)
