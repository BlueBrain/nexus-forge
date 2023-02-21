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
import re, string
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union

from kgforge.core import Resource
from kgforge.core.archetypes import Resolver
from kgforge.core.archetypes.resolver import write_sparql_filters, escape_punctuation
from kgforge.core.commons.exceptions import ResolvingError, ConfigurationError
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

        filter_properties = ['label', 'notation', 'prefLabel', 'altLabel']
        if strategy == strategy.EXACT_MATCH:
            regex = False
            case_insensitive = False
            limit = 1
        elif strategy == strategy.EXACT_CASEINSENSITIVE_MATCH:
            regex = True
            case_insensitive = True
            text = f"^{escape_punctuation(text)}$"
            limit = 1
        else:
            regex = True
            case_insensitive = True
            if strategy == strategy.BEST_MATCH:
                limit = 1
        property_filters = write_sparql_filters(text, filter_properties,
                                                regex, case_insensitive)
        expected_fields = ["type", "label"]
        optional_fields = ["prefLabel", "altLabel", "definition", "subClassOf", "isDefinedBy", "notation"]
        query = _write_resolving_query(first_filters, filter_properties, property_filters,
                                       expected_fields, optional_fields, self.contexts,
                                       resolving_context, limit)
        all_fields = expected_fields + optional_fields
        return self.service.perform_query(query, target, all_fields, limit)

    @staticmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str], **source_config) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, targets: Dict[str, str], **store_config) -> StoreService:
        return StoreService(store, targets, **store_config)


def _write_resolving_query(first_filters: List[str], filter_properties: List[str], property_filters: List[str],
                           expected_fields: List[str], optional_fields: List[str], contexts,
                           resolving_context: Any, limit: Optional[int]):
    """Build the SPARQL query used for resolving.
    
    :param first_filters :
    """
    construct_query_str = "\nCONSTRUCT {\n"
    where_query_str = "WHERE {\n"

    for field in expected_fields:
        if field == 'type':
            construct_query_str += "  ?id a ?type .\n"
            where_query_str += "  ?id a ?type .\n"
        else:
            construct_query_str += """  ?id {0} ?{0} . \n""".format(field)
            where_query_str += """  ?id {0} ?{0} . \n""".format(field)
    for field in optional_fields:
        construct_query_str += """  ?id {0} ?{0} . \n""".format(field)
        where_query_str += "  OPTIONAL { ?id " + "{0} ?{0} .".format(field) + " } \n"

    # if given a context
    if resolving_context:
        context_info = None
        if contexts is None:
            raise ConfigurationError("Contexts to resolve were not found in the configuration.") 
        for context in contexts:
            if context['name'] == resolving_context:
                context_info = context
        if context_info is None:
            raise ConfigurationError("Provided `resolving_context` was not defined in the configuration.") 
        # add context constrain to query
        if context_info['position'] == 'subject':
            where_query_str += """  <{0}> {1} ?id . \n""".format(context_info['value'], context_info['property'])
        elif context_info['position'] == 'object':
            where_query_str += """  ?id {1} <{0}> . \n""".format(context_info['value'], context_info['property'])
        else:
            raise ValueError('Only `subject` or `object` are valid values for the context position.')
    # End query 
    construct_query_str += "} "
    where_query_str += "  {\n"
    select_query_str = "    SELECT * WHERE {\n"
    nprop = len(filter_properties)
    for iprop, pfilter in enumerate(property_filters):
        if iprop+1 == nprop:
            select_query_str += """      {{ {0} ; {2} ?{2} {1} }} \n""".format(first_filters, pfilter, filter_properties[iprop])
        else:
            select_query_str += """      {{ {0} ; {2} ?{2} {1} }} UNION\n""".format(first_filters, pfilter, filter_properties[iprop])
    select_query_str += """    }} LIMIT {0} \n  }}\n}}\n""".format(limit)
    # Add all strings together
    query = construct_query_str + where_query_str + select_query_str
    return query