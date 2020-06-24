# 
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Union

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

    def map(self, data: Any, mapping: Union[Mapping, List[Mapping]], na: Union[Any, List[Any]]
            ) -> Union[Resource, List[Resource]]:
        # Data could be loaded from a directory, a file, a collection, or an object.
        mappings = mapping if isinstance(mapping, List) else [mapping]
        nas = na if isinstance(na, List) else [na]
        if isinstance(data, str):
            path = Path(data)
            if path.is_dir():
                paths = path.iterdir()
                mapped = self._map_many(paths, mappings, nas)
            else:
                mapped = self._map_one(path, mappings, nas)
        elif isinstance(data, (Sequence, Iterator)):
            # NB: Do not use 'Iterable' for checking type because a Dict is an Iterable.
            mapped = self._map_many(data, mappings, nas)
        else:
            mapped = self._map_one(data, mappings, nas)
        return mapped[0] if len(mapped) == 1 else mapped

    def _map_many(self, data: Iterable[Union[Path, Any]], mappings: List[Mapping], nas: List[Any]
                  ) -> List[Resource]:
        # Bulk mapping could be optimized by overriding this method in the specialization.
        # POLICY Should follow self._map_one() policies.
        # POLICY Should not separate records loading for proper parallel / distributed processing.
        return [y for x in data for y in self._map_one(x, mappings, nas)]

    @abstractmethod
    def _map_one(self, data: Union[Path, Any], mappings: List[Mapping], nas: List[Any]
                 ) -> List[Resource]:
        # Method to change to handle a new type of mapping to apply.
        # POLICY Should load the record only one time with self._load_one().
        # POLICY Should not include as Resource properties elements with values in 'na'.
        # POLICY Could make the KnowledgeGraphForge instance available as 'forge'.
        # POLICY Could make the record instance available as 'x'.
        pass

    # No _load_many() for proper parallel / distributed processing directly in self._map_many().

    @staticmethod
    @abstractmethod
    def _load_one(data: Union[Path, Any]) -> Any:
        # Method to change to handle a new type of data to map.
        # POLICY Should prepare the record according to how the rules are using it.
        # The loading cannot be abstracted as it depends on the reader and the rules.
        pass
