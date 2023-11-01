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
import requests
from abc import abstractmethod

from typing import Optional, Union, List, Type
from kgforge.core import Resource
from kgforge.core.archetypes.read_only_store import ReadOnlyStore
from kgforge.core.archetypes.model import Model
from kgforge.core.archetypes.mapping import Mapping
from kgforge.core.archetypes.mapper import Mapper
from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus
from kgforge.core.commons.imports import import_class
from kgforge.core.conversions.json import as_json, from_json


class DatasetStore(ReadOnlyStore):
    """A class to link to external databases, query and search directly on datasets. """

    def __init__(self, model: Optional[Model] = None,
                 ) -> None:
        super().__init__(model)

    @property
    @abstractmethod
    def read_mapper(self) -> Type[Mapper]:
        """Mapper class to map file metadata to a Resource."""
        ...

    @property
    @abstractmethod
    def write_mapper(self) -> Type[Mapper]:
        """Mapper class to map a Resource to the store metadata format."""
        ...

    def map(self, resources: Union[List[Union[Resource, str]], Union[Resource, str]],
            type_: Optional[Union[str, Mapping]] = None, read: bool = True
            ) -> Optional[Union[Resource, List[Resource]]]:
        """ Use mappings to transform resources from and to the store model

        :param resources: data to be transformed
        :param type_: type (schema) of the data
        :param read: set the directionality of the transformations, to use the read_mapper,
                     or the write_mapper
        """
        mappings = self.model.mappings(self.model.source, False)
        if not read:
            mapper = self.write_mapper()
        mapper = self.read_mapper()
        mapped_resources = []
        resources = (resources if isinstance(resources, list) else [resources])
        for resource in resources:
            if isinstance(resource, Resource):
                resource_dict = as_json(resource, expanded=False, store_metadata=False,
                                        model_context=self.model_context,
                                        context_resolver=self.model.resolve_context)
            else:
                resource_dict = resource
                resource = from_json(resource_dict, None)
            if type_ is None:
                try:
                    type_ = resource.type
                except AttributeError:
                    mapped_resources.append(resource)
            elif isinstance(type_, Mapping):
                mapped_resources.append(mapper.map(resource_dict, type_))
            elif type_ in mappings:
                # type_ is the entity here
                mapping_class: Type[Mapping] = import_class(mappings[type_][0], "mappings")
                mapping = self.model.mapping(type_, self.model.source, mapping_class)
                mapped_resources.append(mapper.map(resource_dict, mapping))
            else:
                mapped_resources.append(resource)
        return mapped_resources

    def types(self):
        """Supported data types"""
        # TODO: add other datatypes used, for instance, inside the mappings
        return list(self.model.mappings(self.model.source, False).keys())

    def search(self, resolvers, *filters, **params):
        """Search within the database.

        :param map: bool
        """
        map = params.pop('map', True)
        unmapped_resources = self._search(resolvers, *filters, **params)
        if not map:
            return unmapped_resources
        # Try to find the type of the resources within the filters
        resource_type = type_from_filters(*filters)
        return self.map(unmapped_resources, type_=resource_type)

    @abstractmethod
    def _search(self):
        ...

    def sparql(self, query: str, debug: bool = False, limit: Optional[int] = None,
               offset: Optional[int] = None, **params) -> Optional[Union[List[Resource], Resource]]:
        """Use SPARQL within the database.

        :param map: bool
        """
        map = params.pop('map', True)
        unmapped_resources = self._sparql(query, debug, limit, offset, **params)
        if not map:
            return unmapped_resources
        return self.map(unmapped_resources)

    @abstractmethod
    def _sparql(self, query: str) -> Optional[Union[List[Resource], Resource]]:
        # POLICY Should notify of failures with exception QueryingError including a message.
        # POLICY Resource _store_metadata should not be set (default is None).
        # POLICY Resource _synchronized should not be set (default is False).
        ...


def type_from_filters(*filters) -> Optional[str]:
    """Returns the first `type` found in filters."""
    resource_type = None
    filters = filters[0]
    if isinstance(filters, dict):
        if 'type' in filters:
            resource_type = filters['type']
    else:
        # check filters grouping
        if isinstance(filters, (list, tuple)):
            filters = [filter for filter in filters]
        else:
            filters = [filters]
        for filter in filters:
            if 'type' in filter.path and filter.operator == "__eq__":
                resource_type = filter.value
                break
    return resource_type
