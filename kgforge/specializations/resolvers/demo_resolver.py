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
from itertools import chain
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Union, Any

from kgforge.core.archetypes import Resolver
from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.strategies import ResolvingStrategy
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping


class DemoResolver(Resolver):
    """An example to show how to implement a Resolver and to demonstrate how it is used."""

    def __init__(self, source: str, targets: List[Dict[str, str]], result_resource_mapping: str,
                 **source_config) -> None:
        super().__init__(source, targets, result_resource_mapping, **source_config)

    @property
    def mapping(self) -> Callable:
        return DictionaryMapping

    @property
    def mapper(self) -> Callable:
        return DictionaryMapper

    def _resolve(self, text: Union[str, List[str]], target: Optional[str], type: Optional[str],
                 strategy: ResolvingStrategy, resolving_context: Any, limit: Optional[str], threshold=Optional[float]) -> Optional[List[Dict[str, str]]]:

        if isinstance(text, list):
            not_supported(("text", list))

        resolve_with_properties = None
        if target is not None:
            data = self.service[target]["data"]
            resolve_with_properties = self.service[target]["resolve_with_properties"]
        else:
            data = chain.from_iterable([self.service[target]["data"] for target in self.targets])
        resolve_with_properties = ["label", "acronym"] if resolve_with_properties is None else resolve_with_properties
        if type is not None:
            data = (x for x in data if x.get("type", None) == type)
        if strategy == ResolvingStrategy.EXACT_MATCH:
            try:
                return next(x for x in data
                            if text and any([p in x and text == x[p] for p in resolve_with_properties]))
            except StopIteration:
                return None
        else:
            results = [(_dist([str(x[prop]) for prop in resolve_with_properties if prop in x][0], text), x) for x in data
                       if text and any ([p in x and str(text).lower() in str(x[p]).lower() for p in resolve_with_properties])]
            if results:
                ordered = sorted(results, key=lambda x: x[0])
                if strategy == ResolvingStrategy.BEST_MATCH:
                    return ordered[0][1]
                else:
                    # Case: ResolvingStrategy.ALL_MATCHES.
                    return [x[1] for x in ordered]
            else:
                return None

    @staticmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str], **source_config)\
            -> Dict[str, List[Dict[str, str]]]:
        resolve_with_properties: List[str] = source_config.pop("resolve_with_properties", None)
        if isinstance(resolve_with_properties, str):
            resolve_with_properties = [resolve_with_properties]
        elif resolve_with_properties is not None and not isinstance(resolve_with_properties, list):
            raise ConfigurationError(f"The 'resolve_with_properties' should be a list: {resolve_with_properties} provided.")
        return {target: {"data": list(_load(dirpath, filename)),
                         "resolve_with_properties": resolve_with_properties} for target, filename in targets.items()}


def _dist(x: str, y: str) -> int:
    return len(x) - len(y)


def _load(dirpath: Path, filename: str) -> Iterator[Dict[str, str]]:
    filepath = dirpath / filename
    if filepath.is_file():
        with filepath.open(encoding='utf-8') as f:
            yield from json.load(f)
    else:
        raise ConfigurationError("<source>/<bucket> should be a valid file path")
