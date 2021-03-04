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

# Placeholder for the test suite for wrapping of property paths.

import pytest

from kgforge.core.wrappings.paths import Filter, create_filters_from_dict

@pytest.mark.parametrize("dict_filters, expected", [
        pytest.param(({"agent":{"name":"EPFL"}}),
                     ([Filter(["agent", "name"], "__eq__", "EPFL")]),
                     id="literal"),
        pytest.param(({"agent": {"name": "EPFL", "address":{"postalCode":"1015"}}}),
                     ([Filter(["agent", "name"], "__eq__", "EPFL"),
                       Filter(["agent", "address","postalCode"], "__eq__", "1015")]),
                     id="one_nested"),
        pytest.param(({"type":"Contribution","agent": {"type":"Agent","name": "EPFL", "address": {
                        "type":"PostalAddress","postalCode": "1015","addressCountry":{
                        "type":"Country","name":"Switzerland"}
                        }}}),
                     ([Filter(["type"], "__eq__", "Contribution"),
                       Filter(["agent", "type"], "__eq__", "Agent"),
                       Filter(["agent", "name"], "__eq__", "EPFL"),
                       Filter(["agent", "address", "type"], "__eq__", "PostalAddress"),
                       Filter(["agent", "address", "postalCode"], "__eq__", "1015"),
                       Filter(["agent", "address", "addressCountry","type"], "__eq__", "Country"),
                       Filter(["agent", "address", "addressCountry", "name"], "__eq__", "Switzerland")]),
                     id="many_nested")
    ])
def test_dict_to_filter(dict_filters, expected):
    filters = create_filters_from_dict(dict_filters)
    assert filters == expected
