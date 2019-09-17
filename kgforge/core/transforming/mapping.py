from collections import OrderedDict
from pathlib import Path

import hjson

from kgforge.core.commons.typing import Hjson


# FIXME FIXME FIXME
class Mapping:

    def __init__(self, mapping: Hjson) -> None:
        # FIXME Add used versions of the forge and the model.
        # FIXME Add used mappings for ontology terms and files.
        # FIXME Add used format template for identifiers.
        self.rules: OrderedDict = hjson.loads(mapping)

    def save(self, path: str) -> None:
        # FIXME Should normalize rules representation as Model.template().
        # POLICY Saved rules representation should normalized by being sorted so that:
        # - known keys are sorted like the Model.template() output,
        # - unknown keys are sorted alphabetically in their compacted form (i.e. not IRI or CURIE).
        normalized = hjson.dumps(self.rules, indent=4, sort_keys=True)
        Path(path).write_text(normalized)

    def load(self, path: str) -> "Mapping":
        raise NotImplementedError
