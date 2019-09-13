import json
from typing import Any, Dict, List

from kgforge.core import Resource
from kgforge.core.commons.wrappers import AttrsDict
from kgforge.core.transforming import Mapper, Mapping


# TODO Some parts might be generalized and moved to core/mapping.py, like _apply_rule().
class DictionaryMapper(Mapper):

    def __init__(self, forge, mapping: Mapping) -> None:
        super().__init__(forge, mapping)
        self.reader = json.load

    def apply_one(self, record: Dict) -> Resource:
        variables = {
            "forge": self.forge,
            "x": AttrsDict(record),
        }
        return self._apply_dict(self.mapping.rules, variables)

    def _apply_dict(self, rules: Dict, variables: Dict) -> Resource:
        properties = {k: self._apply_value(v, variables) for k, v in rules.items()}
        return Resource(**properties)

    def _apply_value(self, value: Any, variables: Dict) -> Any:
        if isinstance(value, List):
            return [self._apply_dict(x, variables) for x in value]
        elif isinstance(value, Dict):
            return self._apply_dict(value, variables)
        else:
            return self._apply_rule(value, variables)

    @staticmethod
    def _apply_rule(rule: Any, variables: Dict) -> Any:
        try:
            return eval(rule, {}, variables)
        except (TypeError, NameError, SyntaxError):
            return rule
