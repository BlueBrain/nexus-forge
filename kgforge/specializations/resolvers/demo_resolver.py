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
from pathlib import Path
from typing import Callable, Dict, List, Union

from kgforge.core.archetypes import OntologyResolver, Store
from kgforge.core.resolving import ResolvingStrategy
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping


# FIXME To be refactored while applying the resolving API refactoring.


class DemoResolver(OntologyResolver):
    """An example to show how to implement a Resolver and to demonstrate how it is used."""

    def __init__(self, name: str, source: Union[str, Store], term_resource_mapping: str) -> None:
        super().__init__(name, source, term_resource_mapping)

    @property
    def mapping(self) -> Callable:
        return DictionaryMapping

    @property
    def mapper(self) -> Callable:
        return DictionaryMapper

    def _resolve(self, label: str, type: str, strategy: ResolvingStrategy) -> List[Dict[str, str]]:
        resolved = [(len(x["label"]) - len(label), x) for x in self.service
                    if label in x["label"]]
        ordered = sorted(resolved, key=lambda x: x[0])
        n = 1 if strategy == ResolvingStrategy.BEST_MATCH else len(ordered)
        return [x[1] for x in ordered[:n]]

    @staticmethod
    def _initialize(source: Union[str, Store]) -> Dict[str, str]:
        msg = "DemoResolver supports only ontology data from a file for now."  # TODO
        try:
            filepath = Path(source)
        except TypeError:
            raise NotImplementedError(msg)
        else:
            if not filepath.is_file():
                raise NotImplementedError(msg)
            with filepath.open() as f:
                return json.load(f)
