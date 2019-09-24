from collections import OrderedDict
from pathlib import Path

import hjson

from kgforge.core.commons.attributes import sort_attributes
from kgforge.core.transforming.mapping import Mapping


class DictionaryMapping(Mapping):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @staticmethod
    def load(path: str) -> "DictionaryMapping":
        text = Path(path).read_text()
        return DictionaryMapping(text)

    def _load_rules(self, mapping: str) -> OrderedDict:
        return hjson.loads(mapping)

    def _normalize_rules(self, rules: OrderedDict) -> str:
        return hjson.dumps(rules, indent=4, item_sort_key=sort_attributes)
