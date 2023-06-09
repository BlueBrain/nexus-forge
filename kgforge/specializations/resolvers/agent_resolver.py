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
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union

from kgforge.core.archetypes import Resolver
from kgforge.core.archetypes.resolver import _build_resolving_query
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.sparql_query_builder import SPARQLQueryBuilder
from kgforge.core.commons.strategies import ResolvingStrategy
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.resolvers.store_service import StoreService


class AgentResolver(Resolver):

    def __init__(self, source: str, targets: List[Dict[str, Any]], result_resource_mapping: str,
                 **source_config) -> None:
        super().__init__(source,  targets, result_resource_mapping, **source_config)

    @property
    def mapping(self) -> Callable:
        return DictionaryMapping

    @property
    def mapper(self) -> Callable:
        return DictionaryMapper

    def _resolve(self, text: Union[str, List[str]], target: Optional[str], type: Optional[str],
                 strategy: ResolvingStrategy, resolving_context: Any, limit: Optional[int], threshold: Optional[float]) -> Optional[List[Dict]]:

        if isinstance(text, list):
            not_supported(("text", list))
        
        if target and target not in self.service.sources:
            raise ValueError(f"Unknown target value: {target}. Supported targets for the selected resolvers are: {self.service.sources.keys()}")
        
        properties_to_filter_with = ['name', 'givenName', 'familyName']
        query_template = """
            CONSTRUCT {{
                ?id a ?type ;
                name ?name ;
                givenName ?givenName ;
                familyName ?familyName
            }} WHERE {{
              GRAPH ?g {{
                ?id a ?type .
                OPTIONAL {{
                  ?id name ?name .
                }}
                OPTIONAL {{
                  ?id givenName ?givenName .
                }}
                OPTIONAL {{
                  ?id familyName ?familyName .
                }}
                {{
                  SELECT * WHERE {{
                    {{ {0} ; name ?name {1} }} UNION
                    {{ {0} ; familyName ?familyName; givenName ?givenName {2} }} UNION
                    {{ {0} ; familyName ?familyName; givenName ?givenName {3} }}
                  }} LIMIT {4}
                }}
              }}
            }}
            """
        filters = self.service.filters[target] if target in self.service.filters else None
        context = self.service.get_context(resolving_context, target, filters)
        query, strategy_dependant_limit = _build_resolving_query(text, query_template, self.service.deprecated_property, self.service.filters[target], strategy, type, properties_to_filter_with, context, SPARQLQueryBuilder, limit)
        expected_fields = properties_to_filter_with+["type"]
        return self.service.perform_query(query, target, expected_fields, strategy_dependant_limit)
    
    def _is_target_valid(self, target) -> Optional[bool]:
        return self.service.validate_target(target)

    @staticmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str], **source_config) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, targets: Dict[str, Dict[str, Dict[str, str]]], **store_config) -> StoreService:
        return StoreService(store, targets, **store_config)


