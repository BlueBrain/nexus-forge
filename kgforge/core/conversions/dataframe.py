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

from typing import List, Optional, Union

from pandas import DataFrame

from kgforge.core import Resource
from kgforge.core.commons.execution import catch


@catch
def as_dataframe(data: List[Resource], store_metadata: bool, na: Optional[str],
                 nesting: str) -> DataFrame:
    raise NotImplementedError("not implemented yet")


@catch
def from_dataframe(data: DataFrame, na: Optional[str],
                   nesting: str) -> Union[Resource, List[Resource]]:
    raise NotImplementedError("not implemented yet")
