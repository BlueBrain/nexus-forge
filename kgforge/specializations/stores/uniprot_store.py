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
from pyld import jsonld
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from uuid import uuid4
import requests
from rdflib import Graph
from rdflib.plugins.sparql.parser import Query
from requests import HTTPError
from SPARQLWrapper import SPARQLWrapper, JSON

from kgforge.core import Resource
from kgforge.core.archetypes import Resolver, Store
from kgforge.core.archetypes.store import _replace_in_sparql, rewrite_sparql
# from kgforge.specializations.stores.bluebrain_nexus import (
#     CategoryDataType,
#     build_sparql_query_statements,
#     format_type,
#     _create_select_query
# )
from kgforge.specializations.stores import SPARQLStore
from kgforge.core.commons.context import Context
from kgforge.core.wrappings.dict import DictWrapper
from kgforge.specializations.stores.uniprot.service import Service
from kgforge.core.commons.exceptions import QueryingError
from kgforge.core.commons.execution import not_supported
from kgforge.core.conversions.rdf import as_jsonld, from_jsonld
# from kgforge.core.conversions.json import as_json, from_json
# from kgforge.core.wrappings.dict import wrap_dict
# from kgforge.core.wrappings.paths import create_filters_from_dict
# from urllib.parse import quote_plus, unquote, urlparse, parse_qs
    

UNIPROT_RESTAPI_URL = 'https://rest.uniprot.org/uniprotkb'
UNIPROT_ENTITY_PREFIX = "http://purl.uniprot.org"


class UniProtStore(SPARQLStore):

    """A Store specialized for SPARQL queries, supporting only Reading (searching) methods."""

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None,
                 model_context: Optional[Context] = None,
                 searchendpoints: Optional[Dict] = None,) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping,
                         model_context, searchendpoints)

    @staticmethod
    def resources_from_results(results):
        resources = []
        for result in results:
            resource = {}
            for k, v in result.items():
                if v['type'] =='literal' and ('datatype' in v and v['datatype']=='http://www.w3.org/2001/XMLSchema#boolean'):
                    value = json.loads(str(v["value"]).lower())
                
                elif v['type'] =='literal' and ('datatype' in v and v['datatype']=='http://www.w3.org/2001/XMLSchema#integer'):
                    value = int(v["value"]) 
                # check if the value is an url, if so, get the metadata
                elif v['type'] == 'uri' and UNIPROT_ENTITY_PREFIX in v['value']:
                    value = v["value"]
                    url = UNIPROT_RESTAPI_URL + f"/{value.split('/')[-1]}.json"
                    try:
                        response = requests.get(url)
                        response.raise_for_status()
                    except Exception as e:
                        raise QueryingError(e)
                    else:
                        metadata = response.json()
                        metadata['id'] = value
                        resource[k] = Resource(**metadata)
                else:
                    resource[k] = v['value']
            resources.append(Resource(**resource))
            return resources