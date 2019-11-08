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
        reshaped = (self._reshape(x, keep) for x in resources)
        return Resources(reshaped)

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
