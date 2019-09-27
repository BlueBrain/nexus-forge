import json
import re
from pathlib import Path
from typing import Callable, Dict, List, Union

import hjson

from kgforge.core.commons.actions import run
from kgforge.core.commons.attributes import not_supported, sort_attributes
from kgforge.core.commons.typing import DirPath, Hjson, URL
from kgforge.core.modeling.exceptions import ValidationError
from kgforge.core.modeling.model import Model
from kgforge.core.resources import Resource, Resources
from kgforge.core.storing import Store
from kgforge.core.transforming import Mapping


class DemoModel(Model):
    """This is an implementation of a Model to perform tests and help implement specializations."""

    def __init__(self, source: Union[DirPath, URL, Store]) -> None:
        super().__init__(source)
        self.source = Path(self.source)

    def prefixes(self) -> Dict[str, str]:
        with (self.source / "prefixes.json").open() as f:
            return json.load(f)

    def types(self) -> List[str]:
        with (self.source / "schemas.json").open() as f:
            schemas = json.load(f)
            return [self._compact(x) for x in schemas.keys()]

    def template(self, type: str, only_required: bool = False) -> Hjson:
        if only_required:
            not_supported(("only_required", True))
        else:
            type_expanded = self._expand(type)
            schema = self._schema(type_expanded)
            schema_compacted = self._compact(schema)
            # TODO Example for 'Each nested typed resource should have its template included'.
            for k, v in schema_compacted.items():
                if isinstance(v, Dict):
                    print("NB: DemoStore is not automatically including templates for nested typed resources yet")
            return hjson.dumps(schema_compacted, indent=4, item_sort_key=sort_attributes)

    def mappings(self, source: str) -> Dict[str, List[str]]:
        dirpath = Path(self.source, "mappings", source)
        mappings = {}
        if dirpath.is_dir():
            for x in dirpath.glob("*/*.hjson"):
                mappings.setdefault(x.stem, []).append(x.parent.name)
        return mappings

    def mapping(self, type: str, data_source: str, mapping_type: Callable) -> Mapping:
        filepath = Path(self.source, "mappings", data_source, mapping_type.__name__, f"{type}.hjson")
        return mapping_type.load(filepath)

    def _validate_many(self, resources: Resources) -> None:
        # TODO Example of an optimization for bulk validation.
        run(self._validate, resources, status="_validated")

    def _validate_one(self, resource: Resource) -> None:
        run(self._validate, resource, status="_validated")

    def _validate(self, resource: Resource) -> bool:
        def verify(nested_resource: Resource, nested_schema: Dict) -> None:
            for k, v in nested_schema.items():
                compacted = self._compact(k)
                if isinstance(v, Dict):
                    verify(getattr(nested_resource, compacted), v)
                else:
                    rule = f"{v}(resource, '{compacted}')"
                    try:
                        check = eval(rule, {}, {"resource": nested_resource})
                    except (TypeError, NameError, SyntaxError):
                        pass
                    else:
                        if not check:
                            raise ValidationError(f"{compacted} is missing")
        try:
            type_ = resource.type
        except AttributeError:
            return False
        else:
            type_expanded = self._expand(type_)
            schema = self._schema(type_expanded)
            verify(resource, schema)
            return True

    def _compact(self, value: Union[str, Dict]) -> Union[str, Dict]:
        if isinstance(value, str):
            return re.sub("[a-z]+:", "", value)
        else:
            return {self._compact(k): self._compact(v) for k, v in value.items()}

    def _expand(self, value: str) -> str:
        # FIXME Configure an ontology & Use forge.ontology.resolve() with type="Class" instead.
        with (self.source / "vocabulary.json").open() as f:
            vocabulary = json.load(f)
            return vocabulary[value]

    def _schema(self, type_expanded: str) -> Dict:
        # TODO Example of 'There could be caching but it should be aware of changes made in the source'.
        with (self.source / "schemas.json").open() as f:
            schemas = json.load(f)
            return schemas[type_expanded]
