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
import json
from pathlib import Path
from typing import Any, Optional, Callable, Dict, List, Union

from kgforge.core import Resource
from kgforge.core.commons.context import Context
from kgforge.core.commons.execution import not_supported
from kgforge.core.archetypes import Mapping, Model
from kgforge.core.commons.attributes import repr_class
from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.core.commons.dictionaries import use_values
from kgforge.core.commons.imports import import_class


class Database(ABC):

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/databases/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # POLICY Implementations should pass tests/specializations/databases/test_databases.py.

    def __init__(self, forge : Optional["KnowledgeGraphForge"], source: str, **config) -> None:
        # POLICY Resolver data access should be lazy, unless it takes less than a second.
        # POLICY There could be data caching but it should be aware of changes made in the source.
        self._forge: Optional["KnowledgeGraphForge"] = forge
        # Model
        model_config = config.pop("model")
        if model_config["origin"] == "store":
            use_values(
                model_config,
                config,
                ["endpoint", "token", "bucket", "vocabulary"],
            )
        model_name = model_config.pop("name")
        model = import_class(model_name, "models")
        self._model: Model = model(**model_config)
        self.context = self._model.context()
        if 'model_context' not in config:
            config['model_context'] = self._model.context()
        self.source: str = source
        self.service: Any = self._initialize_service(self.source, **config)

    def __repr__(self) -> str:
        return repr_class(self)

    def map(self, resources : Union[List[Union[Resource, str]], Union[Resource, str]],
            type_ : Optional[Union[str, "DictionaryMapping"]] = None) -> Optional[Union[Resource, List[Resource]]]:
        mappings = self._model.mappings(self._model.source, False)
        mapped_resources = []
        resources = (resources if isinstance(resources, list) else [resources])
        for resource in resources:
            if isinstance(resource, Resource):
               resource_dict = self._forge.as_json(resource) 
            else:
                resource_dict = resource
                resource = self._forge.from_json(resource_dict)
            if type_ is None:
                try:
                    type_ = resource.type
                except AttributeError:
                    mapped_resources.append(resource)
            elif isinstance(type_, Mapping):
                mapped_resources.append(self._forge.map(resource_dict, type_))
            elif type_ in mappings:
                # type_ is the entity here
                mapping_class : Mapping = import_class(mappings[type_][0], "mappings")
                mapping = self._model.mapping(type_, self._model.source, mapping_class)
                mapped_resources.append(self._forge.map(resource_dict, mapping))
            else:
                mapped_resources.append(resource)
        return mapped_resources

    def types(self):
        # TODO: add other datatypes used, for instance, inside the mappings
        return list(self.mappings().keys())

    @abstractmethod
    def search(self, resolvers, *filters, **params) -> Resource:
        pass

    @abstractmethod
    def sparql(self, query: str, debug: bool = False, limit: Optional[int] = None,
               offset: Optional[int] = None,**params) -> Resource:
        pass
    
    @abstractmethod
    def elastic(self, **params) -> Resource:
        pass

    @property
    @abstractmethod
    def health(self) -> Callable:
        """Health of the database."""
        pass

    # Utils.

    def _initialize_service(self, source: str, **source_config) -> Any:
        # Resolver data could be accessed from a directory, a web service, or a Store.
        # Initialize the access to the resolver data according to the source type.
        # POLICY Should not use 'self'. This is not a function only for the specialization to work.
        origin = source_config.pop("origin")
        if origin == "directory":
            dirpath = Path(source)
            return self._service_from_directory(dirpath, **source_config)
        elif origin == "web_service":
            return self._service_from_web_service(source, **source_config)
        elif origin == "store":
            store = import_class(source, "stores")
            if source != 'DemoStore':
                source_config['store_context'] = self.context
            return self._service_from_store(store, **source_config)
        else:
            raise ConfigurationError(f"unrecognized DataBase origin '{origin}'")

    @staticmethod
    def _service_from_directory(dirpath: Path, **source_config) -> Any:
        not_supported()

    @staticmethod
    @abstractmethod
    def _service_from_web_service(endpoint: str, **source_config) -> Any:
        pass

    @staticmethod
    @abstractmethod
    def _service_from_store(store: Callable, **store_config) -> Any:
        pass
