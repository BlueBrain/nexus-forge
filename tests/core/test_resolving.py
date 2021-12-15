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

# Placeholder for the test suite for selection of target or resolver from input and configuration.

from kgforge.core import KnowledgeGraphForge


class TestResolverAsDict:
    """
    Tests the .resolver(as_dict=True) function that returns a dictionary
    """

    def test_resolver_returns_dict(self, config):
        forge = KnowledgeGraphForge(config)
        resolvers_dict = forge.resolvers(as_dict=True)
        assert type(resolvers_dict) is dict

    def test_resolver_returns_correct_object(self, config):
        dict_result = {'terms': {'sex': {'source': 'sex.json'}}}
        forge = KnowledgeGraphForge(config)
        resolvers_dict = forge.resolvers(as_dict=True)
        assert resolvers_dict == dict_result
