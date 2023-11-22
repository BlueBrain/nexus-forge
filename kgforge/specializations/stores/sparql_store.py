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

import requests
from typing import Dict, List, Optional, Union, Any, Type

from kgforge.core import Resource
from kgforge.core.archetypes import Mapper
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.archetypes.model import Model
from kgforge.core.archetypes.dataset_store import DatasetStore
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.stores.sparql.sparql_service import SPARQLService
from kgforge.core.wrappings.paths import create_filters_from_dict
from kgforge.core.wrappings.dict import DictWrapper
from kgforge.core.commons.exceptions import QueryingError
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.sparql_query_builder import SPARQLQueryBuilder
from kgforge.specializations.stores.bluebrain_nexus import (
    _create_select_query
)


class SPARQLStore(DatasetStore):
    """A Store specialized for SPARQL queries, supporting only Reading (searching) methods."""

    def __init__(self, model: Optional[Model] = None,
                 endpoint: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None,
                 searchendpoints: Optional[Dict] = None,
                 **store_config) -> None:
        super().__init__(model)
        self.endpoint = endpoint
        self.file_resource_mapping = file_resource_mapping
        self.searchendpoints = searchendpoints
        self.service = self._initialize_service(endpoint, searchendpoints, **store_config)

    @property
    def mapper(self) -> Optional[Type[Mapper]]:
        return DictionaryMapper

    def _download_one(
        self,
        url: str,
        path: str,
        store_metadata: Optional[DictWrapper],
        cross_bucket: bool,
    ) -> None:
        # path: FilePath.
        # TODO define downloading method
        # POLICY Should notify of failures with exception DownloadingError including a message.
        not_supported()

    def retrieve(
        self, id: str, version: Optional[Union[int, str]], cross_bucket: bool, **params
    ) -> Resource:
        not_supported()

    def _retrieve_filename(self, id: str) -> str:
        not_supported()

    def get_metadata_context(self):
        return self.service.context

    def search(
            self, resolvers: Optional[List["Resolver"]] = None, *filters, **params
    ) -> List[Resource]:
        # Positional arguments in 'filters' are instances of type Filter from wrappings/paths.py
        # A dictionary can be provided for filters:
        #  - {'key1': 'val', 'key2': {'key3': 'val'}} will be translated to
        #  - [Filter(operator='__eq__', path=['key1'], value='val'),
        #     Filter(operator='__eq__', path=['key2', 'key3'], value='val')]
        # Keyword arguments in 'params' could be:
        #   - debug: bool,
        #   - limit: int,
        #   - offset: int,
        #   - deprecated: bool,
        #   - resolving: str, with values in ('exact', 'fuzzy'),
        #   - lookup: str, with values in ('current', 'children').
        # POLICY Should use sparql() and contain 'search_endpoint'.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # POLICY Resource _synchronized should be set to True.
        # pass
        # if self.model_context is None:
        #     raise ValueError("context model missing")
        debug = params.get("debug", False)
        limit = params.get("limit", 100)
        offset = params.get("offset", None)
        distinct = params.get("distinct", False)
        includes = params.get("includes", None)
        excludes = params.get("excludes", None)
        search_endpoint = params.get(
            "search_endpoint", self.service.sparql_endpoint["type"]
        )
        if search_endpoint not in [
            self.service.sparql_endpoint["type"],
        ]:
            raise ValueError(
                f"The provided search_endpoint value '{search_endpoint}' is not supported, only 'sparql'"
            )
        if "filters" in params:
            raise ValueError("A 'filters' key was provided as params. "
                             "Filters should be provided as iterable to be unpacked.")
        if filters and isinstance(filters[0], dict):
            filters = create_filters_from_dict(filters[0])
        filters = list(filters) if not isinstance(filters, list) else filters

        if includes or excludes:
            raise ValueError(
                "Field inclusion and exclusion are not supported when using SPARQL"
            )

        query_statements, query_filters = SPARQLQueryBuilder.build(
                None, resolvers, self.model_context, *filters
            )
        statements = ";\n ".join(query_statements)
        _filters = ".\n".join(query_filters) + '\n'
        _vars = ["?id"]
        query = _create_select_query(
            _vars, f"?id {statements} . \n {_filters}", distinct, False
        )
        # support @id and @type
        resources = self.sparql(query, debug=debug, limit=limit, offset=offset)
        return resources

    def _sparql(self, query: str) -> Optional[Union[Resource, List[Resource]]]:
        try:
            response = requests.post(self.service.sparql_endpoint["endpoint"],
                                     data=query,
                                     headers=self.service.headers_sparql)
            response.raise_for_status()
        except Exception as e:
            raise QueryingError(e) from e

        data = response.json()

        context = self.model_context
        return SPARQLQueryBuilder.build_resource_from_response(query, data, context)

    def _search(self):
        not_supported()

    # Utils.

    def _initialize_service(
        self,
        endpoint: Optional[str],
        searchendpoints: Optional[Dict],
        **store_config,
    ) -> Any:
        try:
            max_connection = store_config.pop("max_connection", 50)
            if max_connection <= 0:
                raise ValueError(
                    f"max_connection value should be great than 0 but {max_connection} is provided"
                )
            content_type = store_config.pop("Content-Type", "application/ld+json")
            accept = store_config.pop("Accept", "application/ld+json")
            params = store_config.pop("params", {})
            store_context = store_config.pop('store_context', None)

        except Exception as ve:
            raise ValueError(f"Store configuration error: {ve}") from ve

        return SPARQLService(
            endpoint=endpoint, model_context=self.model_context,
            store_context=store_context, max_connection=max_connection,
            searchendpoints=searchendpoints,
            content_type=content_type,
            accept=accept, **params
        )
