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
import os
import json
from pathlib import Path, PurePath
from re import I
import copy
from typing import Callable, Optional, Union, Dict, List, Any

from kgforge.core.archetypes import Mapping, Store, Database
from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.dictionaries import with_defaults
from kgforge.core.commons.imports import import_class


class StoreDatabase(Database):
    """A high-level class to retrieve and create Database-related Resources."""
    

    _REQUIRED = ("name", "origin", "source", "model")

    def __init__(self, forge: Optional["KnowledgeGraphForge"], type: str = "Database",
                 **config) -> None:
        """
        The properties defining the StoreDatabase are:

           name: <the name of the database> - REQUIRED
           type: Database - REQUIRED
           origin: <'store'> - REQUIRED
           source: <a directory path, an URL, or the class name of a Store> - REQUIRED
           bucket: <when 'origin' is 'store', a Store bucket>
           endpoint: <when 'origin' is 'store', a Store endpoint>
           token: <when 'origin' is 'store', a Store token
           model:
             origin: <'directory', 'url', or 'store'>
             source: <a directory path, an URL, or the class name of a Store>
             context: <'directory', 'url', or 'store'>
                bucket: <when 'origin' is 'store', a Store bucket>
                iri: <the IRI of the origin>
        """
        self._check_properties(**config)
        self.name = config.pop('name')
        self.type: str = type
        self._forge: Optional["KnowledgeGraphForge"] = forge
        source = config.pop('source')
        super().__init__(source, **config)

    def _check_properties(self, **info):
        properties = info.keys()
        for r in self._REQUIRED:
            if r not in properties:
                raise ValueError(f'Missing {r} from the properties to define the DatabasSource')

    def datatypes(self):
        # TODO: add other datatypes used, for instance, inside the mappings
        return self.mappings().keys()
    
    def search(self, *filters, **params) -> Any:
        self.service.search(*filters, **params)

    def sparql(self, query: str, debug: bool, limit: int = None, offset: int = None, **params) -> Any:
        self.service.sparql(query, debug, limit, offset, **params)

    @staticmethod
    def _service_from_directory(dirpath: Path, **source_config) -> Any:
        not_supported()

    @staticmethod
    def _service_from_web_service(endpoint: str, **source_config) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, **store_config) -> Store:
        # Store.
        print('store config', store_config)
        return store(**store_config)
    
    def health(self) -> Callable:
        not_supported()
