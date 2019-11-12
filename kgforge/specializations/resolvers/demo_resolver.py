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

    def __init__(self, targets: List[Dict[str, str]], source: str,
                 result_resource_mapping: str) -> None:
        super().__init__(targets, source, result_resource_mapping)

    @property
    def mapping(self) -> Callable:
        return DictionaryMapping

    @property
    def mapper(self) -> Callable:
        return DictionaryMapper

    def _resolve(self, text: str, target: Optional[str], type: Optional[str],
                 strategy: ResolvingStrategy) -> Optional[List[Dict[str, str]]]:
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
    def _initialize(source: str, targets: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
        try:
            dirpath = Path(source)
        except TypeError:
            # TODO.
            raise NotImplementedError("DemoResolver supports only resolver data from files"
                                      "in a directory for now.")
        else:
            return {target: list(_load(dirpath, filename)) for target, filename in targets.items()}


def _dist(x: str, y: str) -> int:
    return len(x) - len(y)


def _load(dirpath: Path, filename: str) -> Iterator[Dict[str, str]]:
    filepath = dirpath / filename
    if not filepath.is_file():
        raise ConfigurationError("<source>/<bucket> should be a valid file path")
    with filepath.open() as f:
        yield from json.load(f)
