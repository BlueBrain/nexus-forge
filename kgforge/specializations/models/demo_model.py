# 
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping, Model, Store
from kgforge.core.commons.exceptions import ValidationError


class DemoModel(Model):
    """An example to show how to implement a Model and to demonstrate how it is used."""

    def __init__(self, source: Union[str, Store]) -> None:
        super().__init__(source)

    def prefixes(self) -> Dict[str, str]:
        return self.service.namespaces

    def types(self) -> List[str]:
        return [x["label"] for x in self.service.vocabulary["Class"]]

    def mappings(self, data_source: str) -> Dict[str, List[str]]:
        dirpath = Path(self.source, "mappings", data_source)
        mappings = {}
        if dirpath.is_dir():
            for x in dirpath.glob("*/*.hjson"):
                mappings.setdefault(x.stem, []).append(x.parent.name)
        return mappings

    def mapping(self, type: str, data_source: str, mapping_type: Callable) -> Mapping:
        filename = f"{type}.hjson"
        filepath = Path(self.source, "mappings", data_source, mapping_type.__name__, filename)
        return mapping_type.load(filepath)

    def _template(self, type: str, only_required: bool) -> Dict:
        print("<info> DemoModel does not distinguish values and constraints in templates for now.")  # TODO
        print("<info> DemoModel does not automatically include nested schemas for now.")  # TODO
        if only_required:
            print("<info> DemoModel does not support keeping only required properties for now.")  # TODO
        type_expanded = self.service.expand(type)
        schema = self.service.schema(type_expanded)
        return self.service.compact(schema)

    def _validate_one(self, resource: Resource) -> None:
        # If the resource is not typed, AttributeError is raised: run() sets _validated to False.
        type_ = resource.type
        type_expanded = self.service.expand(type_)
        schema = self.service.schema(type_expanded)
        result, reason = self.service.check(resource, schema)
        if reason is not None:
            raise ValidationError(reason)

    def _initialize(self, source: Union[str, Store]) -> ModelLibrary:
        msg = "DemoModel supports only model data from a directory for now."  # TODO
        try:
            dirpath = Path(self.source)
        except TypeError:
            raise NotImplementedError(msg)
        else:
            if not dirpath.is_dir():
                raise NotImplementedError(msg)
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
