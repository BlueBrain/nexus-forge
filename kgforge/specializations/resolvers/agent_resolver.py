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
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from kgforge.core.archetypes import Resolver
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.strategies import ResolvingStrategy
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.resolvers.store_service import StoreService


class AgentResolver(Resolver):

    def __init__(self, source: str, targets: List[Dict[str, str]], result_resource_mapping: str,
                 **source_config) -> None:
        super().__init__(source,  targets, result_resource_mapping, **source_config)

    @property
    def mapping(self) -> Callable:
        return DictionaryMapping

    @property
    def mapper(self) -> Callable:
        return DictionaryMapper

    def _resolve(self, text: str, target: Optional[str], type: Optional[str],
                 strategy: ResolvingStrategy, limit: Optional[str]) -> Optional[List[Any]]:

        first_filters = f"?id <{self.service.deprecated_property}> \"false\"^^xsd:boolean"
        if type:
            first_filters = f"{first_filters} ; a <{type}>"

        if strategy == strategy.EXACT_MATCH:
            name_filter = f" FILTER (?name = \"{text}\")"
            given_name_filter = f" FILTER (?givenName = \"{text}\")"
            family_name_filter = f" FILTER (?familyName = \"{text}\")"
            limit = 1
        else:
            name_filter = f" FILTER regex(?name, \"{text}\", \"i\")"
            given_name_filter = f" FILTER regex(?givenName, \"{text}\", \"i\")"
            family_name_filter = f" FILTER regex(?familyName, \"{text}\", \"i\")"
            if strategy == strategy.BEST_MATCH:
                limit = 1

        query = """
            CONSTRUCT {{
              ?id a ?type ;
                name ?name ;
                givenName ?givenName ;
                familyName ?familyName
            }} WHERE {{
              ?id a ?type . 
              OPTIONAL {{
                ?id name ?name .
                ?id givenName ?givenName . 
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
            """.format(first_filters, name_filter, given_name_filter, family_name_filter, limit)

        expected_fields = ["type", "name", "familyName", "givenName"]
        return self.service.perform_query(query, target, expected_fields, None)

    @staticmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str]) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, targets: Dict[str, str], **store_config) -> StoreService:
        return StoreService(store, targets, **store_config)

