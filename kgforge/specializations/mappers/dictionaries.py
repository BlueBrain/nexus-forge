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

import json
from typing import Any, Callable, Dict, List

from kgforge.core.commons.wrappers import DictWrapper
from kgforge.core.resources import Resource
from kgforge.core.transforming.mapper import Mapper
from kgforge.core.transforming.mapping import Mapping


class DictionaryMapper(Mapper):

    def __init__(self, forge: "KnowledgeGraphForge") -> None:
        super().__init__(forge)

    def _reader(self) -> Callable:
        return json.load

    def _map_one(self, record: Dict, mapping: Mapping) -> Resource:
        variables = {
            "forge": self.forge,
            "x": DictWrapper(record),
        }
        return self._map_dict(mapping.rules, variables)

    def _map_dict(self, rules: Dict, variables: Dict) -> Resource:
        properties = {k: self._map_value(v, variables) for k, v in rules.items()}
        return Resource(**properties)

    def _map_value(self, value: Any, variables: Dict) -> Any:
        if isinstance(value, List):
            return [self._map_dict(x, variables) for x in value]
        elif isinstance(value, Dict):
            return self._map_dict(value, variables)
        else:
            return self._apply_rule(value, variables)

    @staticmethod
    def _apply_rule(rule: Any, variables: Dict) -> Any:
        # TODO Add support for the full syntax of JSONPath. Need some thinking on the consequences.
        try:
            return eval(rule, {}, variables)
        except (TypeError, NameError, SyntaxError):
            return rule
