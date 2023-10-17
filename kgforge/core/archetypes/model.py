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

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Type

import hjson
from pandas import DataFrame

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping, Store
from kgforge.core.commons.attributes import repr_class, sort_attrs
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import ConfigurationError, ValidationError
from kgforge.core.commons.execution import not_supported, run
from kgforge.core.configs.model_config import ModelConfig, ModelContextConfig
from kgforge.core.configs.store_config import StoreConfig


class Model(ABC):

    # See demo_model.py in kgforge/specializations/models/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/models/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Move from BDD to classical testing to have a more parameterizable test suite. DKE-135.
    # POLICY Implementations should pass tests/specializations/models/demo_model.feature tests.

    def __init__(self, model_config: ModelConfig) -> None:
        # POLICY Model data access should be lazy, unless it takes less than a second.
        # POLICY There could be data caching but it should be aware of changes made in the source.
        self.source: str = model_config.source if isinstance(model_config.source, str) else \
            model_config.source.name
        self.service = self._initialize_service(model_config)

    def __repr__(self) -> str:
        return repr_class(self)

    # Vocabulary.

    def prefixes(self, pretty: bool) -> Optional[Dict[str, str]]:
        prefixes = sorted(self._prefixes().items())
        if pretty:
            print("Used prefixes:")
            df = DataFrame(prefixes)
            formatters = {x: f"{{:<{df[x].str.len().max()}s}}".format for x in df.columns}
            print(df.to_string(header=False, index=False, formatters=formatters))
        else:
            return dict(prefixes)

    def _prefixes(self) -> Dict[str, str]:
        not_supported()

    def types(self, pretty: bool) -> Optional[List[str]]:
        types = sorted(self._types())
        if pretty:
            print(*["Managed entity types:", *types], sep="\n   - ")
        else:
            return types

    @abstractmethod
    def _types(self) -> List[str]:
        # POLICY Should return managed types in their compacted form (i.e. not IRI nor CURIE).
        pass

    def context(self) -> Context:
        # POLICY Should return the context of the Model.
        pass

    def resolve_context(self, iri: str) -> Dict:
        # POLICY Should retrieve the resolved context as dictionary
        not_supported()

    def _generate_context(self) -> Dict:
        # POLICY Should generate the Context from the Model data.
        not_supported()

    # Templates.

    def template(self, type: str, only_required: bool, output: str) -> Optional[Dict]:
        schema = self._template(type, only_required)
        if output == "hjson":
            print(hjson.dumps(schema, indent=4, item_sort_key=sort_attrs))
        elif output == "json":
            print(hjson.dumpsJSON(schema, indent=4, item_sort_key=sort_attrs))
        elif output == "dict":
            return json.loads(hjson.dumpsJSON(schema, item_sort_key=sort_attrs))
        else:
            raise ValueError("unrecognized output")

    @abstractmethod
    def _template(self, type: str, only_required: bool) -> Dict:
        # POLICY Should raise ValueError if 'type' is not managed by the Model.
        # POLICY Each nested typed resource should have its template included.
        # POLICY The value of 'type' and properties should be compacted (i.e. not IRI nor CURIE).
        pass

    # Mappings.

    def sources(self, pretty: bool) -> Optional[List[str]]:
        sources = sorted(self._sources())
        if pretty:
            print(*["Data sources with managed mappings:", *sources], sep="\n   - ")
        else:
            return sources

    def _sources(self) -> List[str]:
        # The discovery strategy cannot be abstracted as it depends on the Model data organization.
        not_supported()

    def mappings(self, source: str, pretty: bool) -> Optional[Dict[str, List[str]]]:
        mappings = {k: sorted(v) for k, v in
                    sorted(self._mappings(source).items(), key=lambda kv: kv[0])}
        if pretty:
            print("Managed mappings for the data source per entity type and mapping type:")
            for k, v in mappings.items():
                print(*[f"   - {k}:", *v], sep="\n        * ")
        else:
            return mappings

    def _mappings(self, source: str) -> Dict[str, List[str]]:
        # POLICY Should raise ValueError if 'source' is not managed by the Model.
        # POLICY Keys should be managed resource types with mappings for the given data source.
        # POLICY Values should be available mapping types for the resource type.
        # The discovery strategy cannot be abstracted as it depends on the Model data organization.
        not_supported()

    def mapping(self, entity: str, source: str, type: Callable) -> Mapping:
        # POLICY Should raise ValueError if 'entity' or 'source' is not managed by the Model.
        # The selection strategy cannot be abstracted as it depends on the Model data organization.
        not_supported()

    # Validation.

    def schema_id(self, type: str) -> str:
        # POLICY Should retrieve the schema id of the given type.
        not_supported()

    def validate(self, data: Union[Resource, List[Resource]],
                 execute_actions_before: bool, type_: str) -> None:
        # Replace None by self._validate_many to switch to optimized bulk validation.
        run(self._validate_one, None, data, execute_actions=execute_actions_before,
            exception=ValidationError, monitored_status="_validated", type_=type_)

    def _validate_many(self, resources: List[Resource], type_: str) -> None:
        # Bulk validation could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._validate_one() and execution._run_one() behaviours.
        not_supported()

    @abstractmethod
    def _validate_one(self, resource: Resource, type_: str) -> None:
        # POLICY Should notify of failures with exception ValidationError including a message.
        pass

    # Utils.

    @classmethod
    def _initialize_service(cls, model_config: ModelConfig) -> Any:
        # Model data could be loaded from a directory, an URL, or a Store.
        # Initialize the access to the model data according to the source type.
        # POLICY Should not use 'self'. This is not a function only for the specialization to work.
        context_iri = model_config.context.iri if model_config.context is not None else None

        if model_config.origin == "directory":
            return cls._service_from_directory(Path(model_config.source), context_iri)
        elif model_config.origin == "url":
            return cls._service_from_url(model_config.source, context_iri)
        elif model_config.origin == "store":
            return cls._service_from_store(model_config)
        else:
            raise ConfigurationError(f"unrecognized Model origin '{model_config.origin}'")

    @classmethod
    @abstractmethod
    def _service_from_directory(cls, dirpath: Path, context_iri: Optional[str]) -> Any:
        ...

    @classmethod
    def _service_from_url(cls, url: str, context_iri: Optional[str]) -> Any:
        raise NotImplementedError()

    @classmethod
    def _service_from_store(
            cls, model_config: ModelConfig
    ) -> Any:
        raise NotImplementedError()
