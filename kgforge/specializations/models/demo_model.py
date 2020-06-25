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
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping, Model
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import ValidationError


class DemoModel(Model):
    """An example to show how to implement a Model and to demonstrate how it is used."""

    def __init__(self, source: str, **source_config) -> None:
        super().__init__(source, **source_config)

    # Vocabulary.

    def _prefixes(self) -> Dict[str, str]:
        return self.service.namespaces

    def _types(self) -> List[str]:
        return [x["label"] for x in self.service.vocabulary["Class"]]

    def context(self) -> Context:
        ctx = {x["label"]: x["id"] for k, v in self.service.vocabulary.items() for x in v}
        return Context({"@context": ctx})

    # Templates.

    def _template(self, type: str, only_required: bool) -> Dict:
        # TODO DKE-148.
        print("<info> DemoModel does not distinguish values and constraints in templates for now.")
        # TODO DKE-148.
        print("<info> DemoModel does not automatically include nested schemas for now.")
        if only_required:
            # TODO DKE-148.
            print("<info> DemoModel does not support keeping only required properties for now.")
        type_expanded = self.service.expand(type)
        schema = self.service.schema(type_expanded)
        return self.service.compact(schema)

    # Mappings.

    def _sources(self) -> List[str]:
        dirpath = Path(self.source, "mappings")
        return [x.stem for x in dirpath.iterdir() if x.is_dir()]

    def _mappings(self, source: str) -> Dict[str, List[str]]:
        dirpath = Path(self.source, "mappings", source)
        mappings = {}
        if dirpath.is_dir():
            for x in dirpath.glob("*/*.hjson"):
                mappings.setdefault(x.stem, []).append(x.parent.name)
        else:
            raise ValueError("unrecognized source")
        return mappings

    def mapping(self, entity: str, source: str, type: Callable) -> Mapping:
        filename = f"{entity}.hjson"
        filepath = Path(self.source, "mappings", source, type.__name__, filename)
        if filepath.is_file():
            return type.load(filepath)
        else:
            raise ValueError("unrecognized entity type or source")

    # Validation.

    def _validate_one(self, resource: Resource) -> None:
        # If the resource is not typed, AttributeError is raised: run() sets _validated to False.
        type_ = resource.type
        type_expanded = self.service.expand(type_)
        schema = self.service.schema(type_expanded)
        result, reason = self.service.check(resource, schema)
        if reason is not None:
            raise ValidationError(reason)

    # Utils.

    @staticmethod
    def _service_from_directory(dirpath: Path, context_iri: str, **dir_config):
        return ModelLibrary(dirpath)


class ModelLibrary:
    """Simulate a third-party library handling interactions with the data used by the model."""

    def __init__(self, dirpath: Path):
        with (dirpath / "namespaces.json").open() as f:
            self.namespaces: Dict[str, str] = json.load(f)
        with (dirpath / "vocabulary.json").open() as f:
            self.vocabulary: Dict = json.load(f)
        with (dirpath / "schemas.json").open() as f:
            self.schemas: Dict = json.load(f)

    def expand(self, value: str) -> str:
        return next(x["id"] for x in self.vocabulary["Class"] if x["label"] == value)

    def compact(self, value: Union[str, Dict]) -> Union[str, Dict]:
        if isinstance(value, Dict):
            return {self.compact(k): self.compact(v) for k, v in value.items()}
        else:
            return re.sub("[a-z]+:", "", value)

    def schema(self, type_expanded: str) -> Dict:
        return self.schemas[type_expanded]

    def check(self, resource: Resource, schema: Dict) -> Tuple[bool, Optional[str]]:
        result, reason = (True, None)
        for k, v in schema.items():
            compacted = self.compact(k)
            if isinstance(v, Dict):
                nested = getattr(resource, compacted)
                result, reason = self.check(nested, v)
                if result is False:
                    return result, reason
            else:
                rule = f"{v}(resource, '{compacted}')"
                try:
                    checked = eval(rule, {}, {"resource": resource})
                except (TypeError, NameError, SyntaxError):
                    pass
                else:
                    if not checked:
                        return False, f"{compacted} is missing"
        else:
            return result, reason
