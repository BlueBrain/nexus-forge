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

from typing import List, Tuple, Union

from kgforge.core import Resource
from kgforge.core.commons.execution import catch


# FIXME To be refactored after the planned introduction of as_graph(), as_rdf() and as_triplets().


@catch
def as_triples(data: Union[Resource, List[Resource]],
               store_metadata: bool) -> List[Tuple[str, str, str]]:
    raise NotImplementedError("not implemented yet")


@catch
def from_triples(data: List[Tuple[str, str, str]]) -> Union[Resource, List[Resource]]:
    raise NotImplementedError("not implemented yet")
