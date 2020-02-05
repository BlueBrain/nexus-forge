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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, List, Optional, Sequence, Union

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping
from kgforge.core.commons.attributes import repr_class


# NB: Do not 'from kgforge.core import KnowledgeGraphForge' to avoid cyclic dependency.


class Mapper(ABC):

    # See dictionaries.py in kgforge/specializations/mappers/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/mappers/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Create a generic parameterizable test suite for mappers. DKE-135.
    # POLICY Implementations should pass tests/specializations/mappers/test_mappers.py.

    def __init__(self, forge: Optional["KnowledgeGraphForge"] = None) -> None:
        self.forge: Optional["KnowledgeGraphForge"] = forge

    def __repr__(self) -> str:
        return repr_class(self)

    @property
    @abstractmethod
    def reader(self) -> Callable:
        pass

    def map(self, data: Any, mapping: Mapping) -> Union[Resource, List[Resource]]:
        # Data could be loaded from a directory, a file, a collection or an object.
        if isinstance(data, str):
            path = Path(data)
            if path.is_dir():
                # Could be optimized by overriding the method in the specialization.
                records = []
                for x in path.iterdir():
                    with x.open() as f:
                        record = self.reader(f)
                        records.append(record)
                return self._map_many(records, mapping)
            else:
                with path.open() as f:
                    record = self.reader(f)
                    return self._map_one(record, mapping)
        elif isinstance(data, (Sequence, Iterator)):
            # NB: Do not use 'Iterable' for checking type because a Dict is an Iterable.
            return self._map_many(data, mapping)
        else:
            return self._map_one(data, mapping)

    def _map_many(self, records: Iterable, mapping: Mapping) -> List[Resource]:
        # Could be optimized by overriding the method in the specialization.
        return [self._map_one(x, mapping) for x in records]

    @abstractmethod
    def _map_one(self, record: Any, mapping: Mapping) -> Resource:
        # POLICY Should give the rules access to the forge as 'forge' and the record as 'x'.
        # TODO Some operations might be abstracted here when other mappers will be implemented.
        pass
