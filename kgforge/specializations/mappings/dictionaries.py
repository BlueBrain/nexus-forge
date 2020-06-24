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

from collections import OrderedDict

import hjson

from kgforge.core.archetypes.mapping import Mapping
from kgforge.core.commons.attributes import sort_attrs


class DictionaryMapping(Mapping):

    def __init__(self, mapping: str) -> None:
        super().__init__(mapping)

    @staticmethod
    def _load_rules(mapping: str) -> OrderedDict:
        return hjson.loads(mapping)

    @staticmethod
    def _normalize_rules(rules: OrderedDict) -> str:
        return hjson.dumps(rules, indent=4, item_sort_key=sort_attrs)
