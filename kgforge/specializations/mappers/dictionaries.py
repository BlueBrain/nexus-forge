import json
from typing import Any, Dict, List

from kgforge.core import Resource
from kgforge.core.commons.wrappers import DictWrapper
from kgforge.core.transforming import Mapper, Mapping


class DictionaryMapper(Mapper):
    reader = json.load

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

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
        try:
            return eval(rule, {}, variables)
        except (TypeError, NameError, SyntaxError):
            return rule
