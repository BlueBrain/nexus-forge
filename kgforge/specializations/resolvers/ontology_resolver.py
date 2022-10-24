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
from typing import List, Dict, Any, Optional, Callable, Union

from kgforge.core import Resource
from kgforge.core.archetypes import Resolver
from kgforge.core.commons.exceptions import ResolvingError
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.strategies import ResolvingStrategy
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

    def _resolve(self, text: Union[str, List[str]], target: Optional[str], type: Optional[str],
                 strategy: ResolvingStrategy, resolving_context: Any, limit: Optional[str], threshold=Optional[float]) \
            -> Optional[List[Dict]]:

        if isinstance(text, list):
            not_supported(("text", list))
        first_filters = f"?id <{self.service.deprecated_property}> \"false\"^^xsd:boolean"
        if type:
            first_filters = f"{first_filters} ; a {type}"

        if strategy == strategy.EXACT_MATCH:
            label_filter = f" FILTER (?label = \"{text}\")"
            notation_filter = f" FILTER (?notation = \"{text}\")"
            prefLabel_filter = f" FILTER (?prefLabel = \"{text}\")"
            altLabel_filter = f" FILTER (?altLabel = \"{text}\")"
            limit = 1
        elif strategy == strategy.EXACT_CASEINSENSITIVE_MATCH:
            label_filter = f" FILTER regex(?label, \"^{text}$\", \"i\")"
            notation_filter = f" FILTER regex(?notation, \"^{text}$\", \"i\")"
            prefLabel_filter = f" FILTER regex(?prefLabel, \"^{text}$\", \"i\")"
            altLabel_filter = f" FILTER regex(?altLabel, \"^{text}$\", \"i\")"
            limit = 1
        else:
            label_filter = f" FILTER regex(?label, \"{text}\", \"i\")"
            notation_filter = f" FILTER regex(?notation, \"{text}\", \"i\")"
            prefLabel_filter = f" FILTER regex(?prefLabel, \"{text}\", \"i\")"
            altLabel_filter = f" FILTER regex(?altLabel, \"{text}\", \"i\")"
            if strategy == strategy.BEST_MATCH:
                limit = 1

        query = """
            CONSTRUCT {{
               ?id a ?type ;
                  label ?label ;
                  prefLabel ?prefLabel ;
                  altLabel ?altLabel ;
                  definition ?definition;
                  subClassOf ?subClassOf ;
                  isDefinedBy ?isDefinedBy ;
                  notation ?notation
            }} WHERE {{
              ?id a ?type ;
                  label ?label ; 
              OPTIONAL {{
                ?id subClassOf ?subClassOf ;
              }}
              OPTIONAL {{
                ?id definition ?definition ;
              }}
              OPTIONAL {{
                ?id prefLabel ?prefLabel .
              }}
              OPTIONAL {{
                ?id altLabel ?altLabel .
              }}
              OPTIONAL {{
                ?id isDefinedBy ?isDefinedBy .
              }}     
              OPTIONAL {{
                ?id notation ?notation .
              }}    
              {{
                SELECT * WHERE {{
                  {{ {0} ; label ?label {1} }} UNION
                  {{ {0} ; notation ?notation {2} }} UNION
                  {{ {0} ; prefLabel ?prefLabel {3} }} UNION
                  {{ {0} ; altLabel ?altLabel {4} }}
                }} LIMIT {5}
              }}
            }}
            """.format(first_filters, label_filter, notation_filter, prefLabel_filter, altLabel_filter, limit)

        expected_fields = ["type", "label", "prefLabel", "subClassOf", "isDefinedBy", "notation"]

        return self.service.perform_query(query, target, expected_fields, limit)

    @staticmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str], **source_config) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, targets: Dict[str, str], **store_config) -> StoreService:
        return StoreService(store, targets, **store_config)
