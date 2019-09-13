from collections import OrderedDict
from pathlib import Path

import hjson

from kgforge.core.commons.typing import Hjson


class Mapping:

    def __init__(self, mapping: Hjson) -> None:
        self.rules: OrderedDict = hjson.loads(mapping)

    def save(self, path: str) -> None:
        # FIXME Put first, recursively, 'type' and 'id' with the 'item_sort_key' argument.
        # FIXME Sort as the templates, with unknown keys sorted alphabetically.
        normalized = hjson.dumps(self.rules, indent=4, sort_keys=True)
        Path(path).write_text(normalized)

    def load(self, path: str) -> "Mapping":
        print("FIXME - Mapping.load()")
        return Mapping("")
