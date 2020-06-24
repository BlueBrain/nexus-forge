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

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from kgforge.core import Resource
from kgforge.core.archetypes import Mapper, Mapping
from kgforge.core.conversions.json import from_json
from kgforge.core.wrappings.dict import DictWrapper, wrap_dict


# NB: Do not 'from kgforge.core import KnowledgeGraphForge' to avoid cyclic dependency.


class DictionaryMapper(Mapper):

    def __init__(self, forge: Optional["KnowledgeGraphForge"] = None) -> None:
        super().__init__(forge)

    def _map_one(self, data: Union[Path, Dict], mappings: List[Mapping], nas: List[Any]
                 ) -> List[Resource]:
        variables = {
            "forge": self.forge,
            "x": self._load_one(data),
        }
        mapped = (_apply_rules(x.rules, variables) for x in mappings)
        return [from_json(x, nas) for x in mapped]

    @staticmethod
    def _load_one(data: Union[Path, Dict]) -> DictWrapper:
        if isinstance(data, Path):
            with data.open() as f:
                record = json.load(f)
                return wrap_dict(record)
        else:
            return wrap_dict(data)


def _apply_rules(value: Any, variables: Dict) -> Union[Dict, List[Dict]]:
    if isinstance(value, Dict):
        return {k: _apply_rules(v, variables) for k, v in value.items()}
    elif isinstance(value, List):
        return [_apply_rules(x, variables) for x in value]
    else:
        # TODO Add support for the full syntax of JSONPath. DKE-147.
        try:
            return eval(value, variables, variables)
        except (TypeError, NameError, SyntaxError):
            return value
