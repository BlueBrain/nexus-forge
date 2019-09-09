import json
from typing import Any, Dict

from kgforge.core.commons import Hjson
from kgforge.core.mapping import Mapper
from kgforge.core.models.resources import Resource


# FIXME Check if inheriting directly from 'dict' is a good idea.
class DictWrapper(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def wrap(data: Any):
        if isinstance(data, Dict):
            return DictWrapper({k: DictWrapper.wrap(v) for k, v in data.items()})
        else:
            return data


# TODO Some parts might be generalized and moved to core/mapping.py, like _apply_rule().
class JsonMapper(Mapper):

    def __init__(self, forge, mapping: Hjson) -> None:
        super().__init__(forge, mapping)
        self.reader = json.load

    def apply_one(self, record: Dict) -> Resource:
        variables = {
            "forge": self.forge,
            "source": DictWrapper(record),
        }
        return self._apply_dict(self.mapping, variables)

    def _apply_dict(self, mapping: Dict, variables: Dict) -> Resource:
        properties = {k: self._apply_value(v, variables) for k, v in mapping.items()}
        return Resource(self.forge, **properties)

    def _apply_value(self, value: Any, variables: Dict) -> Any:
        if isinstance(value, Dict):
            return self._apply_dict(value, variables)
        else:
            return self._apply_rule(value, variables)

    @staticmethod
    def _apply_rule(rule: Any, variables: Dict) -> Any:
        try:
            return eval(rule, {}, variables)
        except (TypeError, NameError, SyntaxError):
            return rule
