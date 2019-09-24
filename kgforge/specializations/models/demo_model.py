import json
import re
from pathlib import Path
from typing import Dict, List, Union

import hjson

from kgforge.core.commons.actions import run
from kgforge.core.commons.attributes import not_supported, sort_attributes
from kgforge.core.commons.typing import Hjson
from kgforge.core.modeling.exceptions import ValidationError
from kgforge.core.modeling.model import Model
from kgforge.core.resources import Resource, Resources


class DemoModel(Model):
    """This is an implementation of a Model to perform tests and help implement specializations."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # TODO Example for 'Model data could be loaded from an URL or the store'.
        self.source = Path(self.source)

    def prefixes(self) -> Dict[str, str]:
        with (self.source / "prefixes.json").open() as f:
            return json.load(f)

    def types(self) -> List[str]:
        with (self.source / "schemas.json").open() as f:
            schemas = json.load(f)
            return [self._compact(x) for x in schemas.keys()]

    def template(self, type: str, only_required: bool = False) -> Hjson:
        # FIXME Example for 'Each nested typed resource should have its template included'.
        if only_required:
            not_supported(("only_required", True))
        else:
            type_expanded = self._expand(type)
            schema = self._schema(type_expanded)
            schema_compacted = self._compact(schema)
            return hjson.dumps(schema_compacted, indent=4, item_sort_key=sort_attributes)

    def _validate_many(self, resources: Resources) -> None:
        # TODO Example of an optimization for bulk validation.
        run(self._validate, resources, status="_validated")

    def _validate_one(self, resource: Resource) -> None:
        run(self._validate, resource, status="_validated")

    def _validate(self, resource: Resource) -> bool:
        try:
            type_ = resource.type
        except AttributeError:
            return False
        else:
            type_expanded = self._expand(type_)
            schema = self._schema(type_expanded)
            for k, v in schema.items():
                # FIXME Validation of nested structures.
                if isinstance(v, Dict):
                    raise NotImplementedError("nested validation not supported yet")
                if k != "rdf:type":
                    prop_compacted = self._compact(k)
                    rule = f"{v}(resource, '{prop_compacted}')"
                    if not eval(rule, {}, {"resource": resource}):
                        raise ValidationError(f"{prop_compacted} is missing")
                    else:
                        return True

    def _compact(self, value: Union[str, Dict]) -> Union[str, Dict]:
        if isinstance(value, str):
            return re.sub("[a-z]+:", "", value)
        else:
            return {self._compact(k): self._compact(v) for k, v in value.items()}

    def _expand(self, value: str) -> str:
        with (self.source / "vocabulary.json").open() as f:
            vocabulary = json.load(f)
            return vocabulary[value]

    def _schema(self, type_expanded: str) -> Dict:
        # TODO Example of 'There could be caching but it should be aware of changes made in the source'.
        with (self.source / "schemas.json").open() as f:
            schemas = json.load(f)
            return schemas[type_expanded]
