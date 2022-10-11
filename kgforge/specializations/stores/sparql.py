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
from kgforge.core.commons.context import Context
from kgforge.core.wrappings.dict import DictWrapper
from kgforge.specializations.stores.uniprot.service import Service
from kgforge.core.commons.exceptions import DownloadingError, QueryingError
from kgforge.core.commons.execution import not_supported
from kgforge.core.conversions.rdf import as_jsonld, from_jsonld


class SPARQLStore(Store):
    """A Store specialized for SPARQL queries, supporting only Reading (searching) methods."""

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None,
                 model_context: Optional[Context] = None,
                 searchendpoints: Optional[Dict] = None,) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping,
                         model_context, searchendpoints)


    # [C]RUD

    def register(self, data: Union[Resource, List[Resource]], schema_id: str = None
    ) -> None:
        # Replace None by self._register_many to switch to optimized bulk registration.
        not_supported()
    
    def _register_one(self, resource: Resource, schema_id: str) -> None:
        not_supported()

    def upload(self, path: str, content_type: str) -> Union[Resource, List[Resource]]:
        not_supported()

    def _upload(path: Path, content_type: str) -> Union[Any, List[Any]]:
        not_supported()

    def _upload_many(self, paths: List[Path], content_type: str) -> List[Any]:
        not_supported()

    def _download_one(
        self,
        url: str,
        path: str,
        store_metadata: Optional[DictWrapper],
        cross_bucket: bool,
    ) -> None:
        # path: FilePath.
        # TODO define dowloading method
        # POLICY Should notify of failures with exception DownloadingError including a message.
        not_supported()

    # C[R]UD

    def retrieve(
        self, id: str, version: Optional[Union[int, str]], cross_bucket: bool, **params
    ) -> Resource:
        not_supported()

    def _retrieve_filename(self, id: str) -> str:
        not_supported() 

    # CR[U]D.

    def update(
        self, data: Union[Resource, List[Resource]], schema_id: Optional[str]
    ) -> None:
        # Replace None by self._update_many to switch to optimized bulk update.
        not_supported()

    def _update_one(self, resource: Resource, schema_id: Optional[str]) -> None:
        not_supported()

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        # Replace None by self._tag_many to switch to optimized bulk tagging.
        # POLICY If tagging modify the resource, run() should have status='_synchronized'.
        not_supported()

    # CRU[D].

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        # Replace None by self._deprecate_many to switch to optimized bulk deprecation.
        not_supported()

    # Querying.

    def search(
        self, resolvers: Optional[List["Resolver"]], *filters, **params
    ) -> List[Resource]:
        # Positional arguments in 'filters' are instances of type Filter from wrappings/paths.py
        # A dictionary can be provided for filters:
        #  - {'key1': 'val', 'key2': {'key3': 'val'}} will be translated to
        #  - [Filter(operator='__eq__', path=['key1'], value='val'), Filter(operator='__eq__', path=['key2', 'key3'], value='val')]
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
        pass
        # if self.model_context is None:
        #     raise ValueError("context model missing")

        # debug = params.get("debug", False)
        # limit = params.get("limit", 100)
        # offset = params.get("offset", None)
        # deprecated = params.get("deprecated", False)
        # distinct = params.get("distinct", False)
        # includes = params.get("includes", None)
        # excludes = params.get("excludes", None)
        # retrieve_source = params.get("retrieve_source")
        # search_endpoint = params.get(
        #     "search_endpoint", self.service.sparql_endpoint["type"]
        # )
        # if search_endpoint not in [
        #     self.service.sparql_endpoint["type"],
        # ]:
        #     raise ValueError(
        #         f"The provided search_endpoint value '{search_endpoint}' is not supported, only 'sparql'"
        #     )
        # if "filters" in params:
        #     raise ValueError("A 'filters' key was provided as params. Filters should be provided as iterable to be unpacked.")


        # if filters and isinstance(filters[0], dict):
        #     filters = create_filters_from_dict(filters[0])
        # filters = list(filters) if not isinstance(filters, list) else filters

        # if includes or excludes:
        #     raise ValueError(
        #         "Field inclusion and exclusion are not supported when using SPARQL"
        #     )

        # query_statements, query_filters = build_sparql_query_statements(
        #     self.model_context, filters
        # )
        # store_metadata_statements = []
        # if retrieve_source:
        #     _vars = ["?id"]
        #     for i, k in enumerate(self.service.store_metadata_keys):
        #         _vars.append(f"?{k}")
        #         store_metadata_statements.insert(i+2, f"<{self.metadata_context.terms[k].id}> ?{k}")
        #     deprecated_filter = f"Filter (?_deprecated = {format_type[CategoryDataType.BOOLEAN](deprecated)})"
        #     query_filters.append(deprecated_filter)
        # else:
        #     _vars = ["?id", "?_project", "?_rev"]
        #     store_metadata_statements.append(f"<{self.service.revision_property}> ?_rev")
        #     store_metadata_statements.append(f"<{self.service.project_property}> ?_project")
        #     query_statements.append(
        #         f"<{self.service.deprecated_property}> {format_type[CategoryDataType.BOOLEAN](deprecated)}",
        #     )
        # query_statements.extend(store_metadata_statements)
        # statements = ";\n ".join(query_statements)
        # _filters = "\n".join(".\n ".join(query_filters))
        # query = _create_select_query(
        #     _vars, f"?id {statements} . \n {_filters}", distinct
        # )
        # # support @id and @type
        # resources = self.sparql(query, debug=debug, limit=limit, offset=offset)
        # params_retrieve = deepcopy(self.service.params.get("retrieve", {}))
        # params_retrieve['retrieve_source'] = retrieve_source
        # results = self.service.batch_request(
        #     resources, BatchAction.FETCH, None, QueryingError, params=params_retrieve
        # )
        # resources = list()
        # for result in results:
        #     resource = result.resource
        #     if retrieve_source:
        #         store_metadata_response = as_json(result.resource, expanded=False, store_metadata=False,
        #                                           model_context=None,
        #                                           metadata_context=None,
        #                                           context_resolver=None)  # store_metadata is obtained from SPARQL (resource) and not from server (response) because of retrieve_source==True
        #     else:
        #         store_metadata_response = result.response  # dict
        #     try:
        #         resource = self.service.to_resource(result.response)
        #     except Exception as e:
        #         self.service.synchronize_resource(
        #             resource, store_metadata_response, self.search.__name__, False, False
        #         )
        #         raise ValueError(e)
        #     finally:
        #         self.service.synchronize_resource(
        #             resource, store_metadata_response, self.search.__name__, True, False
        #         )
        #     resources.append(resource)
        # return resources

    def sparql(
        self, query: str, debug: bool, limit: int = None, offset: int = None, **params
    ) -> List[Resource]:
        rewrite = params.get("rewrite", True)
        qr = (
            rewrite_sparql(query, self.model_context, self.service.metadata_context)
            if self.model_context is not None and rewrite
            else query
        )
        qr = _replace_in_sparql(qr, "LIMIT", limit, 100, r" LIMIT \d+")
        qr = _replace_in_sparql(qr, "OFFSET", offset, 0, r" OFFSET \d+")
        if debug:
            self._debug_query(qr)
        return self._sparql(qr, limit, offset, **params)

    def _sparql(self, query: str, limit: int, offset: int = None, **params) -> List[Resource]:
        try:
            wrapper = SPARQLWrapper(self.service.sparql_endpoint["endpoint"])
            wrapper.setQuery(query)
            wrapper.setReturnFormat(JSON)
            response = wrapper.query()
        except Exception as e:
            raise QueryingError(e)
        else:
            data = response.convert()
            # FIXME workaround to parse a CONSTRUCT query, this fix depends on
            #  https://github.com/BlueBrain/nexus/issues/1155
            _, q_comp = Query.parseString(query)
            if q_comp.name == "ConstructQuery":
                subject_triples = {}
                for r in data["results"]["bindings"]:
                    subject = r["subject"]["value"]
                    s = f"<{r['subject']['value']}>"
                    p = f"<{r['predicate']['value']}>"
                    if r["object"]["type"] == "uri":
                        o = f"<{r['object']['value']}>"
                    else:
                        if "datatype" in r["object"]:
                            o = f"\"{r['object']['value']}\"^^{r['object']['datatype']}"
                        else:
                            o = f"\"{r['object']['value']}\""
                    if subject in subject_triples:
                        subject_triples[subject] += f"\n{s} {p} {o} . "
                    else:
                        subject_triples[subject] = f"{s} {p} {o} . "

                def triples_to_resource(iri, triples):
                    graph = Graph().parse(data=triples, format="nt")
                    data_expanded = json.loads(graph.serialize(format="json-ld"))
                    data_expanded = json.loads(graph.serialize(format="json-ld"))
                    frame = {"@id": iri}
                    data_framed = jsonld.frame(data_expanded, frame)
                    context = self.model_context or self.context
                    compacted = jsonld.compact(data_framed, context.document)
                    resource = from_jsonld(compacted)
                    resource.context = (
                        context.iri
                        if context.is_http_iri()
                        else context.document["@context"]
                    )
                    return resource

                return [triples_to_resource(s, t) for s, t in subject_triples.items()]

            else:
                # SELECT QUERY
                results = data["results"]["bindings"]
                return self.resources_from_results(results)

    @staticmethod
    def resources_from_results(results):
        return [
            Resource(**{k: json.loads(str(v["value"]).lower()) if v['type'] =='literal' and
                                                                  ('datatype' in v and v['datatype']=='http://www.w3.org/2001/XMLSchema#boolean')
                                                               else (int(v["value"]) if v['type'] =='literal' and
                                                                     ('datatype' in v and v['datatype']=='http://www.w3.org/2001/XMLSchema#integer')
                                                                     else v["value"]
                                                                     )
                        for k, v in x.items()} )
            for x in results
        ]

    def elastic(
        self, query: str, debug: bool, limit: int, offset: int
    ) -> List[Resource]:
        not_supported()

    # Versioning.

    def freeze(self, data: Union[Resource, List[Resource]]) -> None:
        not_supported()

    def _freeze_one(self, resource: Resource) -> None:
        not_supported()

    # Utils.

    def _initialize_service(
        self,
        endpoint: Optional[str],
        bucket: Optional[str],
        token: Optional[str],
        searchendpoints: Optional[Dict] = None,
        **store_config,
    ) -> Any:
        try:
            max_connection = store_config.pop("max_connection", 50)
            if max_connection <= 0:
                raise ValueError(
                    f"max_connection value should be great than 0 but {max_connection} is provided"
                )
            store_context_config = store_config.pop("vocabulary", {})
            content_type = store_config.pop("Content-Type", "application/ld+json")
            accept = store_config.pop("Accept", "application/ld+json")
            params = store_config.pop("params", {})
        except Exception as ve:
            raise ValueError(f"Store configuration error: {ve}")
        else:
            return Service(endpoint=endpoint, model_context=self.model_context, max_connection=max_connection,
                           searchendpoints=searchendpoints, content_type=content_type, accept=accept, **params)

    @staticmethod
    def _debug_query(query):
        if isinstance(query, Dict):
            print("Submitted query:", query)
        else:
            print(*["Submitted query:", *query.splitlines()], sep="\n   ")
        print()