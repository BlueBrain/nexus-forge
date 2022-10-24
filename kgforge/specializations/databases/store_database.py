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
from pathlib import Path, PurePath
from re import I
import copy
from typing import Callable, Optional, Union, Dict, List, Any

from kgforge.core import Resource
from kgforge.core.archetypes import Store, Database
from kgforge.core.commons.execution import not_supported
from kgforge.core.wrappings.paths import FilterOperator
from kgforge.specializations.mappers.dictionaries import DictionaryMapper
from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus


class StoreDatabase(Database):
    """A high-level class to retrieve and create Database-related Resources."""
    

    _REQUIRED = ("name", "origin", "source", "model")

    def __init__(self, forge: Optional["KnowledgeGraphForge"],
                 **config) -> None:
        """
        The properties defining the StoreDatabase are:

        :param forge: To use forge utilities 
           name: <the name of the database> - REQUIRED
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
        source = config.pop('source')
        super().__init__(forge, source, **config)

    def _check_properties(self, **info):
        properties = info.keys()
        for r in self._REQUIRED:
            if r not in properties:
                raise ValueError(f'Missing {r} from the properties to define the DatabasSource')


    def search(self, resolvers, *filters, **params):
        """Search within the database.

        :param keep_original: bool 
        """
        keep_original = params.pop('keep_original', True)
        unmapped_resources = self.service.search(resolvers, *filters, **params)
        if isinstance(self.service, BlueBrainNexus) or keep_original:
            return unmapped_resources
        else:
            # Try to find the type of the resources within the filters
            resource_type = type_from_filters(filters)
            return self.map_resources(unmapped_resources, resource_type=resource_type)

        return resource_type
    
    def sparql(self, query: str, debug: bool = False, limit: Optional[int] = None, 
               offset: Optional[int] = None,**params):
        """Use SPARQL within the database.

        :param keep_original: bool 
        """
        keep_original = params.pop('keep_original', True)
        unmapped_resources = self.service.sparql(query, debug, limit, offset, **params)
        if keep_original:
            return unmapped_resources
        else:
            return self.map_resources(unmapped_resources)
    
    def elastic(**params):
        not_supported()
    
    @staticmethod
    def _service_from_web_service(endpoint: str, **source_config) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, **store_config) -> Store:
        return store(**store_config)
    
    def health(self) -> Callable:
        not_supported()

def type_from_filters(filters):
    resource_type = None
    if isinstance(filters[0], dict):
        if 'type' in filters[0]:
            resource_type = filters[0]['type']
    else:
        for filter in filters:
            if 'type' in filter.path and filter.operator is FilterOperator.EQUAL:
                resource_type = filter.value
                break
    return resource_type