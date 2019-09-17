from typing import Any, Callable, Dict, List

from pandas import DataFrame

from kgforge.core import Resource, Resources
from kgforge.core.commons.typing import ManagedData
from kgforge.core.transforming import Mapping
from kgforge.core.transforming.reshaping import _reshape


class TransformingInterface:

    def __init__(self, forge):
        self.forge = forge

    def map(self, data: Any, mapper: Callable, mapping: Mapping) -> ManagedData:
        return mapper(self.forge).map(data, mapping)

    def reshape(self, data: ManagedData, keep: List[str], versioned: bool = False) -> ManagedData:
        # POLICY Resource _last_action and _store_metadata should be None.
        # POLICY Resource _validated and _synchronized should be False.
        # FIXME Use ResourceMapper instead.
        def _process(resource: Resource, keep, versioned) -> Resource:
            r = _reshape(resource, keep)
            if versioned:
                self.forge.store.freeze_links(r)
            return r
        if isinstance(data, Resources):
            return Resources(_process(x, keep, versioned) for x in data)
        else:
            return _process(data, keep, versioned)

    def as_json(self, expanded: bool = False, store_metadata: bool = False) -> Dict:
        if expanded:
            return self.as_jsonld(False, store_metadata)
        else:
            data = self.as_jsonld(True, store_metadata)
            del data["@context"]
            return data

    def as_jsonld(self, compacted: bool = True, store_metadata: bool = False) -> Dict:
        raise NotImplementedError

    def as_dataframe(self, store_metadata: bool = False) -> DataFrame:
        raise NotImplementedError
