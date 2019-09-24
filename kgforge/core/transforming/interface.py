from typing import Any, Callable, Dict, List, Tuple, Union

from pandas import DataFrame

from kgforge.core.commons.typing import ManagedData
from kgforge.core.transforming.converters import Converters
from kgforge.core.transforming.mapping import Mapping
from kgforge.core.transforming.reshaper import Reshaper


class TransformingInterface:

    def __init__(self, forge: "KnowledgeGraphForge") -> None:
        self.forge: "KnowledgeGraphForge" = forge

    def map(self, data: Any, mapper: Callable, mapping: Mapping) -> ManagedData:
        return mapper(self.forge).map(data, mapping)

    def reshape(self, data: ManagedData, keep: List[str], versioned: bool = False) -> ManagedData:
        return Reshaper(self.forge).reshape(data, keep, versioned)

    def as_json(self, data: ManagedData, expanded: bool = False, store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return Converters.as_json(data, expanded, store_metadata)

    def as_jsonld(self, data: ManagedData, compacted: bool = True, store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return Converters.as_jsonld(data, compacted, store_metadata)

    def as_triples(self, data: ManagedData, store_metadata: bool = False) -> List[Tuple[str, str, str]]:
        return Converters.as_triples(data, store_metadata)

    def as_dataframe(self, data: ManagedData, store_metadata: bool = False) -> DataFrame:
        return Converters.as_dataframe(data, store_metadata)
