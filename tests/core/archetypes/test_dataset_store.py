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

from kgforge.core.wrappings.paths import Filter
from kgforge.core.archetypes.dataset_store import type_from_filters


@pytest.mark.parametrize(
    "filters,expected",
    [
        pytest.param(
            [{'type': 'Person'}],
            'Person',
            id="dictionary_type",
        ),
        pytest.param(
            [{'id': 'my_id'}],
            None,
            id="dictionary_notype",
        ),
        pytest.param(
            [Filter(['id'], '__eq__', 'some_id')],
            None,
            id="one_filter_notype",
        ),
        pytest.param(
            [Filter(['type'], '__eq__', 'Person')],
            'Person',
            id="one_filter_type",
        ),
        pytest.param(
            [Filter(['id'], '__eq__', 'some_id'), Filter(['label'], '__eq__', 'some_label')],
            None,
            id="two_filters_notype",
        ),
        pytest.param(
            [Filter(['id'], '__eq__', 'some_id'), Filter(['type'], '__eq__', 'Person')],
            'Person',
            id="two_filters_type",
        ),
        pytest.param(
            [Filter(['type'], '__eq__', 'Protein'), Filter(['type'], '__eq__', 'Person')],
            'Protein',
            id="two_filters_two_types",
        ),
    ]
)
def test_type_from_filters(filters, expected):
    assert type_from_filters(filters) == expected