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
from kgforge.core.commons.execution import not_supported


class DictionaryMapping(Mapping):

    def __eq__(self, other: object) -> bool:
        # FIXME To properly work the loading of rules should normalize them. DKE-184.
        # return eq_class(self, other)
        raise not_supported()

    @staticmethod
    def _load_rules(mapping: str) -> OrderedDict:
        return hjson.loads(mapping)

    @staticmethod
    def _normalize_rules(rules: OrderedDict) -> str:
        return hjson.dumps(rules, indent=4, item_sort_key=sort_attrs)

    @classmethod
    def load_str(cls, source: str, raise_ex=True):
        # hjson loading doesn't make one line strings (non dictionaries) fail
        if len(source.strip()) > 0 and source.strip()[0] != "{":
            if raise_ex:
                raise hjson.scanner.HjsonDecodeError(
                    "Invalid hjson mapping", doc=source, pos=0
                )
            return None
        return cls(source)
