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
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from kgforge.core.archetypes import Resolver
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.strategies import ResolvingStrategy
from kgforge.core.conversions.json import as_json
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.resolvers.store_service import StoreService


class OntologyResolver(Resolver):

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

        statements = [
            f"?id <{self.service.deprecated_property}> \"false\"^^xsd:boolean",
            "?id label ?label",
            "?id a Class",
            "?id a ?type",
            """ 
            OPTIONAL {
                ?id prefLabel ?prefLabel ;  
                    subClassOf ?subClassOf ;  
                    isDefinedBy ?isDefinedBy ;
                    notation ?notation
            }
            """
        ]

        if type:
            statements.append(f"?id a <{type}>")

        if strategy == strategy.EXACT_MATCH:
            statements.append(f" FILTER (?label = \"{text}\")")
            limit = 1
        elif strategy == strategy.BEST_MATCH:
            statements.append(f" FILTER regex(?label, \"{text}\", \"i\")")
            limit = 1
        elif strategy == strategy.ALL_MATCHES:
            statements.append(f" FILTER regex(?label, \"{text}\", \"i\")")

        query = f"""
            CONSTRUCT {{
                ?id a ?type ;
                    label ?label ;
                    prefLabel ?prefLabel ;
                    subClassOf ?subClassOf ;
                    isDefinedBy ?isDefinedBy ;
                    notation ?notation
            }}
            WHERE {{{ ' . '.join(statements) }}}
            """

        expected_fields = ["type", "label", "prefLabel", "subClassOf", "isDefinedBy", "notation"]

        return self.service.perform_query(query, target, expected_fields, limit)

    @staticmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str]) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, targets: Dict[str, str], **store_config) -> StoreService:
        return StoreService(store, targets, **store_config)



