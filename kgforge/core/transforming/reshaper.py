from typing import List

from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData, dispatch
from kgforge.core.resources import Resource, Resources


class Reshaper:

    def __init__(self, forge: "KnowledgeGraphForge") -> None:
        self.forge = forge

    @catch
    def reshape(self, data: ManagedData, keep: List[str], versioned: bool = False) -> ManagedData:
        # POLICY Resource _last_action and _store_metadata should be None.
        # POLICY Resource _validated and _synchronized should be False.
        if versioned:
            self.forge._store.freeze(data)
        return dispatch(data, self._reshape_many, self._reshape_one, keep)

    def _reshape_many(self, resources: Resources, keep: List[str]) -> Resources:
        return Resources(self._reshape(x, keep) for x in resources)

    def _reshape_one(self, resource: Resource, keep: List[str]) -> Resource:
        return self._reshape(resource, keep)

    def _reshape(self, resource: Resource, keep: List[str]) -> Resource:
        levels = [x.split(".", maxsplit=1) for x in keep]
        roots = {x[0] for x in levels}
        new = Resource()
        for root in roots:
            leafs = [x[1] for x in levels if len(x) > 1 and x[0] == root]
            value = getattr(resource, root)
            if isinstance(value, Resources):
                new_value = self._reshape_many(value, leafs)
            elif isinstance(value, Resource):
                if leafs:
                    new_value = self._reshape_one(value, leafs)
                else:
                    attributes = value.__dict__.items()
                    properties = {k: v for k, v in attributes if k not in value._RESERVED}
                    new_value = Resource(**properties)
            else:
                new_value = value
            setattr(new, root, new_value)
        return new
