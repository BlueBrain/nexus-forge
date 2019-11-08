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
from typing import Any, Callable, Iterator, Sequence, Union

from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData
from kgforge.core.resources import Resource, Resources
from kgforge.core.transforming.mapping import Mapping


class Mapper(ABC):

    # See dictionaries.py in kgforge/specializations/mappers for an implementation.

    def __init__(self, forge: "KnowledgeGraphForge") -> None:
        self.forge = forge

    @property
    @abstractmethod
    def _reader(self) -> Callable:
        pass

    @catch
    def map(self, data: Any, mapping: Mapping) -> ManagedData:
        # Data could be loaded from a directory, a file, a collection or an object.
        if isinstance(data, str):
            path = Path(data)
            reader = self._reader()
            if path.is_dir():
                # Could be optimized by overriding the method in the specialization.
                records = []
                for x in path.iterdir():
                    with x.open() as f:
                        record = reader(f)
                        records.append(record)
                return self._map_many(records, mapping)
            else:
                with path.open() as f:
                    record = reader(f)
                    return self._map_one(record, mapping)
        elif isinstance(data, (Sequence, Iterator)):
            return self._map_many(data, mapping)
        else:
            return self._map_one(data, mapping)

    def _map_many(self, records: Union[Sequence, Iterator], mapping: Mapping) -> Resources:
        # Could be optimized by overriding the method in the specialization.
        mapped = (self._map_one(x, mapping) for x in records)
        return Resources(*mapped)

    @abstractmethod
    def _map_one(self, record: Any, mapping: Mapping) -> Resource:
        # POLICY Should give the rules access to the forge as 'forge' and the record as 'x'.
        pass
