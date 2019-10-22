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

from typing import Any, Callable, Dict, List, Tuple, Union

from pandas import DataFrame

from kgforge.core.commons.typing import ManagedData
from kgforge.core.transforming.converters import Converters
from kgforge.core.transforming.mapping import Mapping
from kgforge.core.transforming.reshaper import Reshaper


class TransformingInterface:

    def __init__(self, forge: "KnowledgeGraphForge") -> None:
        self.forge = forge

    def map(self, data: Any, mapper: Callable, mapping: Mapping) -> ManagedData:
        return mapper(self.forge).map(data, mapping)

    def reshape(self, data: ManagedData, keep: List[str], versioned: bool = False) -> ManagedData:
        return Reshaper(self.forge).reshape(data, keep, versioned)

    @staticmethod
    def as_json(data: ManagedData, expanded: bool = False, store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return Converters.as_json(data, expanded, store_metadata)

    @staticmethod
    def as_jsonld(data: ManagedData, compacted: bool = True, store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return Converters.as_jsonld(data, compacted, store_metadata)

    @staticmethod
    def as_triples(data: ManagedData, store_metadata: bool = False) -> List[Tuple[str, str, str]]:
        return Converters.as_triples(data, store_metadata)

    @staticmethod
    def as_dataframe(data: ManagedData, store_metadata: bool = False) -> DataFrame:
        return Converters.as_dataframe(data, store_metadata)
