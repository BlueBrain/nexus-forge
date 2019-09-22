import re
from typing import Dict, List

import hjson

from kgforge.core.commons.actions import Actions, run
from kgforge.core.commons.typing import Hjson, ManagedData, dispatch
from kgforge.core.modeling.exceptions import ValidationError
from kgforge.core.modeling.model import Model
from kgforge.core.resources import Resource, Resources


class DemoModel(Model):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # FIXME Should demo the loading from a directory, an URL, or the store.
        # Demo implementation.
        self.source = {
            "prefixes": {
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "schema": "http://schema.org/",
            },
            "vocabulary": {
                "Person": "schema:Person",
            },
            "schemas": {
                "schema:Person": {
                    "rdf:type": "schema:Person",
                    "schema:name": "hasattr",
                }
            }
        }

    def prefixes(self) -> Dict[str, str]:
        # Demo implementation.
        return self.source["prefixes"]

    def types(self) -> List[str]:
        # Demo implementation.
        return [self._compact(x) for x in self.source["schemas"].keys()]

    def template(self, type: str, only_required: bool = False) -> Hjson:
        # Demo implementation.
        # FIXME Should order 'type' and 'id' first.
        type_expanded = self._expand(type)
        schema = {self._compact(k): v for k, v in self._schema(type_expanded).items()}
        schema["type"] = type
        return hjson.dumps(schema, indent=4, sort_keys=True)

    def validate(self, data: ManagedData) -> None:
        dispatch(data, self._validate_many, self._validate_one)

    def _validate_many(self, resources: Resources) -> None:
        for x in resources:
            run(self._validate, "_validated", x)
        print(Actions.from_resources(resources))

    def _validate_one(self, resource: Resource) -> None:
        run(self._validate, "_validated", resource)
        print(resource._last_action)

    # Demo implementation.
    def _validate(self, resource: Resource) -> bool:
        try:
            type_ = resource.type
        except AttributeError:
            return False
        else:
            type_expanded = self._expand(type_)
            schema = self._schema(type_expanded)
            for k, v in schema.items():
                if k != "rdf:type":
                    prop_compacted = self._compact(k)
                    rule = f"{v}(resource, '{prop_compacted}')"
                    if not eval(rule, {}, {"resource": resource}):
                        raise ValidationError(f"{prop_compacted} is missing")
                    else:
                        return True

    # Demo implementation.
    def _compact(self, value: str) -> str:
        return re.sub("[a-z]+:", "", value)

    # Demo implementation.
    def _expand(self, value: str) -> str:
        return self.source["vocabulary"][value]

    # Demo implementation.
    def _schema(self, type_expanded: str) -> Dict:
        return self.source["schemas"][type_expanded]
