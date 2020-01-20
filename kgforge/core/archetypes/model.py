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
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import hjson

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping
from kgforge.core.commons.attributes import repr_class, sort_attrs
from kgforge.core.commons.exceptions import ConfigurationError, ValidationError
from kgforge.core.commons.execution import not_supported, run


class Model(ABC):

    # See demo_model.py in kgforge/specializations/models/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/models/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Move from BDD to classical testing to have a more parameterizable test suite. DKE-135.
    # POLICY Implementations should pass tests/specializations/models/demo_model.feature tests.

    def __init__(self, source: str, **source_config) -> None:
        # POLICY Model data access should be lazy, unless it takes less than a second.
        # POLICY There could be data caching but it should be aware of changes made in the source.
        self.source: str = source
        self.service: Any = self._initialize_service(self.source, **source_config)

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

    def template(self, type: str, only_required: bool, output: str) -> Optional[Dict]:
        schema = self._template(type, only_required)
        if output == "hjson":
            print(hjson.dumps(schema, indent=4, item_sort_key=sort_attrs))
        elif output == "json":
            print(hjson.dumpsJSON(schema, indent=4, item_sort_key=sort_attrs))
        elif output == "dict":
            return schema
        else:
            raise ValueError("unrecognized output")

    @abstractmethod
    def _template(self, type: str, only_required: bool) -> Dict:
        # POLICY Should raise ValueError if 'type' is not managed by the Model.
        # POLICY Each nested typed resource should have its template included.
        # POLICY The value of 'type' and properties should be compacted (i.e. not IRI nor CURIE).
        pass

    # Mappings.

    # FIXME To be refactored while applying the mapping API refactoring. DKE-104.
    def mappings(self, data_source: str) -> Dict[str, List[str]]:
        # The discovery strategy cannot be abstracted as it depends of the Model data organization.
        # POLICY Should raise ValueError if 'data_source' is not managed by the Model.
        # POLICY Keys should be managed types with mappings for the given data source.
        # POLICY Values should be available mapping types for the resource type.
        not_supported()

    # FIXME To be refactored while applying the mapping API refactoring. DKE-104.
    def mapping(self, type: str, data_source: str, mapping_type: Callable) -> Mapping:
        # POLICY Should raise ValueError if 'data_source' is not managed by the Model.
        # The selection strategy cannot be abstracted as it depends of the Model data organization.
        not_supported()

    # Validation.

    def validate(self, data: Union[Resource, List[Resource]],
                 execute_actions_before: bool) -> None:
        # Replace None by self._validate_many to switch to optimized bulk validation.
        run(self._validate_one, None, data, execute_actions=execute_actions_before,
            exception=ValidationError, monitored_status="_validated")

    def _validate_many(self, resources: List[Resource]) -> None:
        # Bulk validation could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._validate_one() and execution._run_one() behaviours.
        not_supported()

    @abstractmethod
    def _validate_one(self, resource: Resource) -> None:
        # POLICY Should notify of failures with exception ValidationError including a message.
        pass

    # Utils.

    def _initialize_service(self, source: str, **source_config) -> Any:
        # Model data could be loaded from a directory, an URL, or a Store.
        # Initialize the access to the model data according to the source type.
        # POLICY Should not use 'self'. This is not a function only for the specialization to work.
        stores = import_module("kgforge.specializations.stores")
        if hasattr(stores, source):
            return self._service_from_store(source, **source_config)
        else:
            try:
                dirpath = Path(source)
            except TypeError:
                return self._service_from_url(source)
            else:
                if dirpath.is_dir():
                    return self._service_from_directory(dirpath)
                else:
                    raise ConfigurationError("source should be a valid directory path")

    @staticmethod
    @abstractmethod
    def _service_from_directory(dirpath: Path) -> Any:
        not_supported()

    @staticmethod
    def _service_from_url(url: str) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store_name: str, **store_config) -> Any:
        not_supported()
