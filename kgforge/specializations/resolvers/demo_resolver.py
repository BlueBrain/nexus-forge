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
from typing import Callable, Dict, Iterator, List, Optional

from kgforge.core.archetypes import Resolver
from kgforge.core.commons.exceptions import ConfigurationError
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

    def _resolve(self, text: str, target: Optional[str], type: Optional[str],
                 strategy: ResolvingStrategy, limit: Optional[str]) -> Optional[List[Dict[str, str]]]:
        if target is not None:
            data = self.service[target]
        else:
            data = chain.from_iterable(self.service.values())

        if type is not None:
            data = (x for x in data if x.get("type", None) == type)

        if strategy == ResolvingStrategy.EXACT_MATCH:
            try:
                return next(x for x in data
                            if text == x["label"] or ("acronym" in x and text == x["acronym"]))
            except StopIteration:
                return None
        else:
            results = [(_dist(x["label"], text), x) for x in data
                       if text and text in x["label"] or ("acronym" in x and text in x["acronym"])]
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
    def _service_from_directory(dirpath: Path, targets: Dict[str, str]
                                ) -> Dict[str, List[Dict[str, str]]]:
        return {target: list(_load(dirpath, filename)) for target, filename in targets.items()}


def _dist(x: str, y: str) -> int:
    return len(x) - len(y)


def _load(dirpath: Path, filename: str) -> Iterator[Dict[str, str]]:
    filepath = dirpath / filename
    if filepath.is_file():
        with filepath.open() as f:
            yield from json.load(f)
    else:
        raise ConfigurationError("<source>/<bucket> should be a valid file path")
