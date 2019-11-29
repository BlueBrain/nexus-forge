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
from typing import Any, Callable, Dict, List, Union

import hjson

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping, Store
from kgforge.core.commons.attributes import repr_class, sort_attrs
from kgforge.core.commons.execution import not_supported, run


class Model(ABC):

    # See demo_model.py in kgforge/specializations/models/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/models/__init__.py.
    # POLICY Implementations should not add methods in the derived class.
    # TODO Move from BDD to classical testing to have a more parameterizable test suite. DKE-135.
    # POLICY Implementations should pass tests/specializations/models/demo_model.feature tests.

    def __init__(self, source: Union[str, Store]) -> None:
        # source: Union[DirPath, URL, Store].
        # POLICY Model data access should be lazy, unless it takes less than a second.
        # POLICY There could be data caching but it should be aware of changes made in the source.
        self.source: Union[str, Store] = source
        self.service: Any = self._initialize(self.source)

    def __repr__(self) -> str:
        return repr_class(self)

    # Vocabulary.

    def prefixes(self) -> Dict[str, str]:
        not_supported()

    @abstractmethod
    def types(self) -> List[str]:
        # POLICY Should return managed types in their compacted form (i.e. not IRI nor CURIE).
        pass

    # Templates.

    def template(self, type: str, only_required: bool) -> str:
        # Return Hjson.
        # POLICY Each nested typed resource should have its template included.
        # POLICY The value of 'type' and properties should be compacted (i.e. not IRI nor CURIE).
        schema = self._template(type, only_required)
        return hjson.dumps(schema, indent=4, item_sort_key=sort_attrs)

    @abstractmethod
    def _template(self, type: str, only_required: bool) -> Dict:
        pass

    # Mappings.

    # FIXME To be refactored while applying the mapping API refactoring. DKE-104.
    def mappings(self, data_source: str) -> Dict[str, List[str]]:
        # The discovery strategy cannot be abstracted as it depends of the Model data organization.
        # POLICY Keys should be managed types with mappings for the given data source.
        # POLICY Values should be available mapping types for the resource type.
        not_supported()

    # FIXME To be refactored while applying the mapping API refactoring. DKE-104.
    def mapping(self, type: str, data_source: str, mapping_type: Callable) -> Mapping:
        # The selection strategy cannot be abstracted as it depends of the Model data organization.
        not_supported()

    # Validation.

    def validate(self, data: Union[Resource, List[Resource]]) -> None:
        # Replace None by self._validate_many to switch to optimized bulk validation.
        run(self._validate_one, None, data, status="_validated")

    def _validate_many(self, resources: List[Resource]) -> None:
        # Bulk validation could be optimized by overriding this method in the specialization.
        # POLICY Should follow self._validate_one() policies.
        # POLICY Should reproduce execution._run_one() behaviour with the arguments given to run().
        not_supported()

    @abstractmethod
    def _validate_one(self, resource: Resource) -> None:
        # POLICY Should notify of failures with exception ValidationError including a message.
        pass

    # Utils.

    @abstractmethod
    def _initialize(self, source: Union[str, Store]) -> Any:
        # source: Union[DirPath, URL, Store].
        # POLICY Should initialize the access to the model data according to the source type.
        # Model data could be loaded from a directory, an URL, or the store.
        pass
