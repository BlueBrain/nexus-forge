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
from typing import Any, Callable, List, Union

from kgforge.core import Resource
from kgforge.core.archetypes import Store
from kgforge.core.commons.attributes import repr_class
from kgforge.core.commons.execution import catch
from kgforge.core.resolving import ResolvingStrategy


# FIXME To be refactored while applying the resolving API refactoring. DKE-128 + DKE-105.


class OntologyResolver(ABC):

    # See demo_resolver.py in kgforge/specializations/resolvers/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/resolvers/__init__.py.
    # POLICY Implementations should not add methods in the derived class.
    # TODO Create a generic parameterizable test suite for resolvers. DKE-135.
    # POLICY Implementations should pass tests/specializations/resolvers/test_resolvers.py.

    def __init__(self, name: str, source: Union[str, Store], term_resource_mapping: str) -> None:
        # POLICY Resolver data access should be lazy, unless it takes less than a second.
        # POLICY There could be data caching but it should be aware of changes made in the source.
        self.name: str = name
        self.source: Union[str, Store] = source
        self.service: Any = self._initialize(self.source)
        self.term_mapping: Any = self.mapping.load(term_resource_mapping)

    def __repr__(self) -> str:
        return repr_class(self)

    @property
    @abstractmethod
    def mapping(self) -> Callable:
        """Mapping class to load term_resource_mapping."""
        pass

    @property
    @abstractmethod
    def mapper(self) -> Callable:
        """Mapper class to map term or entity metadata to a Resource with term_resource_mapping."""
        pass

    @catch
    def resolve(self, label: str, type: str,
                strategy: ResolvingStrategy) -> Union[Resource, List[Resource]]:
        # The resolving strategy cannot be abstracted as it should be managed by the service.
        resolved = self._resolve(label, type, strategy)
        if len(resolved) == 1:
            resolved = resolved[0]
        return self.mapper().map(resolved, self.term_mapping)

    @abstractmethod
    def _resolve(self, label: str, type: str, strategy: ResolvingStrategy) -> List[Any]:
        # POLICY Should notify of failures with exception ResolvingError including a message.
        pass

    @staticmethod
    @abstractmethod
    def _initialize(ontology_source: Union[str, Store]) -> Any:
        # ontology_source: Union[FilePath, URL, Store].
        # POLICY Should initialize the access to the ontology data according to the source type.
        # Ontology data could be loaded from a file, an URL, or the store.
        # TODO Some operations might be abstracted here when other resolvers will be implemented.
        pass
