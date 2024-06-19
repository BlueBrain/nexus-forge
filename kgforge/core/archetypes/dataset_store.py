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

from abc import abstractmethod

from typing import Optional, Union, List, Type, Dict
from kgforge.core.resource import Resource
from kgforge.core.archetypes.read_only_store import ReadOnlyStore
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.archetypes.mapping import Mapping
from kgforge.core.archetypes.mapper import Mapper
from kgforge.core.commons.imports import import_class
from kgforge.core.conversions.json import as_json, from_json
from kgforge.core.wrappings import Filter


class DatasetStore(ReadOnlyStore):
    """A class to link to external databases, query and search directly on datasets. """

    @property
    @abstractmethod
    def mapper(self) -> Type[Mapper]:
        """Mapper class to map a Resource to the store metadata format."""
        ...

    def map(self, resources: Union[List[Union[Resource, str]], Union[Resource, str]],
            type_: Optional[Union[str, Mapping]] = None,
            ) -> Optional[Union[Resource, List[Resource]]]:
        """ Use mappings to transform resources from and to the store model

        :param resources: data to be transformed
        :param type_: type (schema) of the data
        """
        mappings = self.model.mappings(self.model.source, False)
        mapper = self.mapper()
        mapped_resources = []
        resources = (resources if isinstance(resources, list) else [resources])
        for resource in resources:
            if isinstance(resource, Resource):
                resource_dict = as_json(resource, expanded=False, store_metadata=False,
                                        model_context=self.model_context(),
                                        metadata_context=None,
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

    def types(self) -> Optional[List[str]]:
        """Supported data types"""
        # TODO: add other datatypes used, for instance, inside the mappings
        return list(self.model.mappings(self.model.source, False).keys())

    def search(
            self, *filters: Union[Dict, Filter],
            resolvers: Optional[List[Resolver]] = None,
            **params
    ) -> Optional[List[Resource]]:
        """
        Search within the database.
        """
        filters = list(filters)
        unmapped_resources = self._search(filters, resolvers, **params)

        if not params.pop('map', True):
            return unmapped_resources
        # Try to find the type of the resources within the filters
        resource_type = type_from_filters(filters)
        return self.map(unmapped_resources, type_=resource_type)

    @abstractmethod
    def _search(
            self, filters: List[Union[Dict, Filter]], resolvers: Optional[List[Resolver]] = None,
            **params
    ) -> Optional[List[Resource]]:
        ...

    def sparql(
            self, query: str, debug: bool = False, limit: Optional[int] = None,
            offset: Optional[int] = None, **params
    ) -> Optional[Union[List[Resource], Resource]]:
        """
        Use SPARQL within the database.
        """
        unmapped_resources = super().sparql(query, debug, limit, offset, **params)

        if not params.pop('map', True):
            return unmapped_resources

        return self.map(unmapped_resources)


def type_from_filters(filters: List[Union[Filter, Dict]]) -> Optional[str]:
    """Returns the first `type` found in filters."""

    filters = list(filters) if isinstance(filters, (list, tuple)) else [filters]

    for f in filters:
        if isinstance(f, dict):
            if 'type' in f:
                return f['type']
        elif isinstance(f, Filter):
            if 'type' in f.path and f.operator == "__eq__":
                return f.value
        else:
            raise ValueError("Invalid filter type: Can only be a Dict or Filter")

    return None
