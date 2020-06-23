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

import json
import mimetypes
import re
from asyncio import Task
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from urllib.parse import quote_plus, unquote

import nexussdk as nexus
import requests
from pyld import jsonld
from rdflib import Graph
from rdflib.plugins.sparql.parser import Query
from requests import HTTPError
from enum import Enum

from kgforge.core import Resource
from kgforge.core.archetypes import Store
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import (DeprecationError, DownloadingError, RegistrationError,
                                             RetrievalError, TaggingError, UpdatingError,
                                             UploadingError)
from kgforge.core.commons.exceptions import (QueryingError)
from kgforge.core.commons.execution import run
from kgforge.core.conversions.rdf import as_jsonld, from_jsonld
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.stores.nexus.service import Service, BatchAction, DEPRECATED_PROPERTY


class CategoryDataType(Enum):
    NUMBER = "number"
    BOOLEAN = "boolean"
    LITERAL = "literal"


type_map = {
    str: CategoryDataType.LITERAL,
    bool:  CategoryDataType.BOOLEAN,
    int: CategoryDataType.NUMBER,
    float: CategoryDataType.NUMBER,
    complex: CategoryDataType.NUMBER
}

format_type = {
    CategoryDataType.NUMBER: lambda x: x,
    CategoryDataType.LITERAL: lambda x: f"\"{x}\"",
    CategoryDataType.BOOLEAN: lambda x: "true" if x is True else "false"
}

operator_map = {
    "__lt__": "<",
    "__le__": "<=",
    "__eq__": "=",
    "__ne__": "!=",
    "__gt__": ">",
    "__ge__": ">=",
}


class BlueBrainNexus(Store):

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None,
                 model_context: Optional[Context] = None) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping,
                         model_context)

    @property
    def mapping(self) -> Optional[Callable]:
        return DictionaryMapping

    @property
    def mapper(self) -> Optional[Callable]:
        return DictionaryMapper

    def register(self, data: Union[Resource, List[Resource]], schema_id: str = None) -> None:
        run(self._register_one, self._register_many, data, required_synchronized=False,
            execute_actions=True, exception=RegistrationError, monitored_status="_synchronized",
            schema_id=schema_id)

    def _register_many(self, resources: List[Resource], schema_id: str) -> None:

        def register_callback(task: Task):
            result = task.result()
            if isinstance(result.response, Exception):
                self.service.synchronize_resource(
                    result.resource, result.response, self._register_many.__name__, False, False)
            else:
                result.resource.id = result.response["@id"]
                if not hasattr(result.resource, "context"):
                    context = self.model_context or self.context
                    result.resource.context = context.iri if context.is_http_iri() else context.document["@context"]
                self.service.synchronize_resource(
                    result.resource, result.response, self._register_many.__name__, True, True)

        verified = self.service.verify(
            resources, self._register_many.__name__, RegistrationError, id_required=False,
            required_synchronized=False, execute_actions=True)
        self.service.batch_request(
            verified, BatchAction.CREATE, register_callback, RegistrationError, schema_id=schema_id)

    def _register_one(self, resource: Resource, schema_id: str) -> None:
        context = self.model_context or self.context
        data = as_jsonld(resource, "compacted", False, model_context=context,
                         metadata_context=None, context_resolver=self.service.resolve_context)
        try:
            response = nexus.resources.create(org_label=self.organisation,
                                              project_label=self.project, data=data,
                                              schema_id=schema_id)
        except nexus.HTTPError as e:
            raise RegistrationError(_error_message(e))
        else:
            resource.id = response['@id']
            # If resource had no context, update it with the one provided by the store.
            if not hasattr(resource, "context"):
                resource.context = data["@context"]
            self.service.sync_metadata(resource, response)

    def _upload_one(self, filepath: Path, content_type: str) -> Dict:
        file = str(filepath.absolute())
        mime_type = content_type or mimetypes.guess_type(file, True)[0]
        if mime_type is None:
            mime_type = "application/octet-stream"
        try:
            response = nexus.files.create(self.organisation, self.project, file,
                                          content_type=mime_type)
        except HTTPError as e:
            raise UploadingError(_error_message(e))
        else:
            return response

    # C[R]UD.

    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        try:
            if isinstance(version, int):
                response = nexus.resources.fetch(org_label=self.organisation,
                                                 project_label=self.project,
                                                 resource_id=id, rev=version)
            elif isinstance(version, str):
                response = nexus.resources.fetch(org_label=self.organisation,
                                                 project_label=self.project,
                                                 resource_id=id, tag=version)
            else:
                response = nexus.resources.fetch(org_label=self.organisation,
                                                 project_label=self.project,
                                                 resource_id=id)
        except HTTPError as e:
            raise RetrievalError(_error_message(e))
        else:
            resource = self.service.to_resource(response)
            resource._synchronized = True
            self.service.sync_metadata(resource, response)
            return resource

    def _download_one(self, url: str, path: Path) -> None:
        try:
            # this is a hack since _self and _id have the same uuid
            file_id = url.split("/")[-1]
            if file_id.startswith("http"):
                file_id = unquote(file_id).split("/")[-1]
            if len(file_id) < 1:
                raise DownloadingError("Invalid file name")
            nexus.files.fetch(org_label=self.organisation, project_label=self.project,
                              file_id=file_id, out_filepath=str(path))
        except HTTPError as e:
            raise DownloadingError(_error_message(e))

    # CR[U]D.

    def update(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._update_one, self._update_many, data, id_required=True, required_synchronized=False,
            execute_actions=True, exception=UpdatingError, monitored_status="_synchronized")

    def _update_many(self, resources: List[Resource]) -> None:
        update_callback = self.service.default_callback(self._update_many.__name__)
        verified = self.service.verify(
            resources, self._update_many.__name__, UpdatingError, id_required=True,
            required_synchronized=False, execute_actions=True)
        self.service.batch_request(verified, BatchAction.UPDATE, update_callback, UpdatingError)

    def _update_one(self, resource: Resource) -> None:
        context = self.model_context or self.context
        data = as_jsonld(resource, "compacted", False, model_context=context, metadata_context=None,
                         context_resolver=self.service.resolve_context)
        rev = {"rev": resource._store_metadata._rev}
        url = f"{self.service.url_resources}/_/{quote_plus(resource.id)}"
        try:
            response = requests.put(url, headers=self.service.headers,
                                    data=json.dumps(data, ensure_ascii=True), params=rev)
            response.raise_for_status()
        except HTTPError as e:
            raise UpdatingError(_error_message(e))
        else:
            self.service.sync_metadata(resource, response.json())

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        run(self._tag_one, self._tag_many, data, id_required=True, required_synchronized=True,
            exception=TaggingError, value=value)

    def _tag_many(self, resources: List[Resource], value: str) -> None:
        tag_callback = self.service.default_callback(self._tag_many.__name__)
        verified = self.service.verify(
            resources, self._tag_many.__name__, TaggingError, id_required=True,
            required_synchronized=True, execute_actions=False)
        self.service.batch_request(
            verified, BatchAction.TAG, tag_callback, TaggingError, tag=value)

    def _tag_one(self, resource: Resource, value: str) -> None:
        data = {
            "tag": value,
            "rev": resource._store_metadata._rev
        }
        url = f"{self.service.url_resources}/_/{ quote_plus(resource.id)}/tags?rev={resource._store_metadata._rev}"
        try:
            response = requests.post(url, headers=self.service.headers,
                                     data=json.dumps(data, ensure_ascii=True))
            response.raise_for_status()
        except HTTPError as e:
            raise TaggingError(_error_message(e))
        else:
            self.service.sync_metadata(resource, response.json())

    # CRU[D].

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._deprecate_one, self._deprecate_many, data, id_required=True,
            required_synchronized=True, exception=DeprecationError, monitored_status="_synchronized")

    def _deprecate_many(self, resources: List[Resource]) -> None:
        deprecate_callback = self.service.default_callback(self._deprecate_many.__name__)
        verified = self.service.verify(
            resources, self._deprecate_many.__name__, DeprecationError, id_required=True,
            required_synchronized=True, execute_actions=False)
        self.service.batch_request(
            verified, BatchAction.DEPRECATE, deprecate_callback, DeprecationError)

    def _deprecate_one(self, resource: Resource) -> None:
        url = f"{self.service.url_resources}/_/{ quote_plus(resource.id)}?rev={resource._store_metadata._rev}"
        try:
            response = requests.delete(url, headers=self.service.headers)
            response.raise_for_status()
        except HTTPError as e:
            raise DeprecationError(_error_message(e))
        else:
            self.service.sync_metadata(resource, response.json())

    # Querying.

    def search(self, resolvers: Optional[List["Resolver"]], *filters, **params) -> List[Resource]:

        if self.model_context is None:
            raise ValueError("context model missing")

        debug = params.get("debug", False)
        limit = params.get("limit", 100)
        offset = params.get("offset", None)
        deprecated = params.get("deprecated", False)
        query_statements, query_filters = build_query_statements(self.model_context, filters)
        query_statements.insert(0, f"<{DEPRECATED_PROPERTY}> {format_type[CategoryDataType.BOOLEAN](deprecated)}")
        statements = "\n".join((";\n ".join(query_statements), ".\n ".join(query_filters)))

        query = f"SELECT ?id WHERE {{ ?id {statements}}}"
        resources = self.sparql(query, debug=debug, limit=limit, offset=offset)
        results = self.service.batch_request(resources, BatchAction.FETCH, None, QueryingError)
        resources = list()
        for result in results:
            resource = result.resource
            try:
                resource = self.service.to_resource(result.response)
            except Exception as e:
                self.service.synchronize_resource(
                    resource, result.response, self.search.__name__, False, False)
                raise ValueError(e)
            finally:
                self.service.synchronize_resource(
                    resource, result.response, self.search.__name__, True, True)
            resources.append(resource)
        return resources

    def _sparql(self, query: str, limit: int, offset: int = None) -> List[Resource]:

        s_offset = "" if offset is None else f"OFFSET {offset}"
        s_limit = "" if limit is None else f"LIMIT {limit}"
        query = f"{query} {s_limit} {s_offset}"

        try:
            response = requests.post(
                self.service.sparql_endpoint, data=query, headers=self.service.headers_sparql)
            response.raise_for_status()
        except Exception as e:
            raise QueryingError(e)
        else:
            data = response.json()
            # FIXME workaround to parse a CONSTRUCT query, this fix depends on
            #  https://github.com/BlueBrain/nexus/issues/1155
            _, q_comp = Query.parseString(query)
            if q_comp.name == "ConstructQuery":
                subject_triples = {}
                for r in data["results"]["bindings"]:
                    subject = r['subject']['value']
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
                    data_expanded = json.loads(graph.serialize(format="json-ld").decode("utf-8"))
                    frame = {"@id": iri}
                    data_framed = jsonld.frame(data_expanded, frame)
                    context = self.model_context or self.context
                    compacted = jsonld.compact(data_framed, context.document)
                    resource = from_jsonld(compacted)
                    resource.context = context.iri if context.is_http_iri() else context.document["@context"]
                    return resource

                return [triples_to_resource(s, t) for s, t in subject_triples.items()]

            else:
                # SELECT QUERY
                results = data["results"]["bindings"]
                return [Resource(**{k: v["value"] for k, v in x.items()}) for x in results]

    # Utils.

    def _initialize_service(self, endpoint: Optional[str], bucket: Optional[str],
                            token: Optional[str]) -> Any:
        try:
            self.organisation, self.project = self.bucket.split('/')
        except ValueError:
            raise ValueError("malformed bucket parameter, expecting 'organization/project' like")
        else:
            return Service(endpoint, self.organisation, self.project, token, self.model_context, 200)


def _error_message(error: HTTPError) -> str:

    def format_message(msg):
        return "".join([msg[0].lower(), msg[1:-1], msg[-1] if msg[-1] != "." else ""])

    try:
        reason = error.response.json()["reason"]
        return format_message(reason)
    except AttributeError:
        pass
    try:
        return format_message(error.response.text())
    except AttributeError:
        return format_message(str(error))


def build_query_statements(context: Context, *conditions) -> Tuple[List,List]:
    statements = list()
    filters = list()
    for index, f in enumerate(*conditions):
        try:
            last_term = context.terms[f.path[-1]]
        except KeyError:
            last_term = ""

        if f.path[-1] == "id":
            f.path.pop()

        property_path = "/".join(f.path)

        if f.path[-1] == "type" or last_term.type == "@id":
            if f.operator == "__eq__":
                statements.append(f"{property_path} {f.value}")
            elif f.operator == "__ne__":
                statements.append(f"{property_path} ?v{index}")
                filters.append(f"FILTER(?v{index} != {f.value})")
            else:
                raise NotImplementedError(f"operator '{f.operator}' is not supported in this query")
        else:
            value_type = type_map[type(f.value)]
            value = format_type[value_type](f.value)
            if value_type is CategoryDataType.LITERAL:
                statements.append(f"{property_path} ?v{index}")
                filters.append(f"FILTER(?v{index} = {value})")
                # filters.append(f"{property_path} ?v{index} FILTER regex(?v{index}, {value})")
            else:
                statements.append(f"{property_path} ?v{index}")
                filters.append(f"FILTER(?v{index} {operator_map[f.operator]} {value})")

    return statements, filters

