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

from typing import List, Union

from kgforge.core import Resource
from kgforge.core.commons.attributes import repr_class
from kgforge.core.commons.execution import catch, dispatch


class Reshaper:

    # This class is not intended to be specialized.

    def __init__(self, versioned_id_template: str) -> None:
        self.versioned_id_template: str = versioned_id_template

    def __repr__(self) -> str:
        return repr_class(self)

    @catch
    def reshape(self, data: Union[Resource, List[Resource]], keep: List[str],
                versioned: bool) -> Union[Resource, List[Resource]]:
        # POLICY Resource _last_action and _store_metadata should be None.
        # POLICY Resource _validated and _synchronized should be False.
        return dispatch(data, self._reshape_many, self._reshape_one, keep, versioned)

    def _reshape_many(self, resources: List[Resource], keep: List[str],
                      versioned: bool) -> List[Resource]:
        # Could be optimized in the future.
        return [self._reshape(x, keep, versioned) for x in resources]

    def _reshape_one(self, resource: Resource, keep: List[str], versioned: bool) -> Resource:
        return self._reshape(resource, keep, versioned)

    def _reshape(self, resource: Resource, keep: List[str], versioned: bool) -> Resource:
        # TODO Use as base an implementation of JSONPath for Python. DKE-147.
        levels = [x.split(".", maxsplit=1) for x in keep]
        roots = {x[0] for x in levels}
        new = Resource()
        for root in roots:
            leafs = [x[1] for x in levels if len(x) > 1 and x[0] == root]
            value = getattr(resource, root)
            if isinstance(value, List):
                new_value = self._reshape_many(value, leafs, versioned)
            elif isinstance(value, Resource):
                if leafs:
                    new_value = self._reshape_one(value, leafs, versioned)
                else:
                    attributes = value.__dict__.items()
                    properties = {k: v for k, v in attributes if k not in value._RESERVED}
                    new_value = Resource(**properties)
            else:
                if root == "id" and versioned:
                    new_value = self.versioned_id_template.format(x=resource)
                else:
                    new_value = value
            setattr(new, root, new_value)
        return new
