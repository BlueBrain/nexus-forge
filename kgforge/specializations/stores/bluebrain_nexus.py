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

import asyncio
import json
import mimetypes
import re
from asyncio import Semaphore, Task
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import quote_plus, unquote, urlparse, parse_qs

import nexussdk as nexus
import requests
from aiohttp import ClientSession, MultipartWriter
from aiohttp.hdrs import CONTENT_DISPOSITION, CONTENT_TYPE
from numpy import nan
from pyld import jsonld
from rdflib import Graph
from rdflib.plugins.sparql.parser import Query

from requests import HTTPError

from kgforge.core import Resource
from kgforge.core.archetypes import Store
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import (DeprecationError, DownloadingError, QueryingError,
                                             RegistrationError, RetrievalError, TaggingError,
                                             UpdatingError, UploadingError)
from kgforge.core.commons.execution import run, not_supported
from kgforge.core.commons.files import is_valid_url
from kgforge.core.conversions.rdf import as_jsonld, from_jsonld
from kgforge.core.wrappings.dict import DictWrapper
from kgforge.core.wrappings.paths import Filter, create_filters_from_dict
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.stores.nexus.service import BatchAction, Service


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
                 model_context: Optional[Context] = None, searchendpoints:Optional[Dict] = None, **store_config) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping,
                         model_context, searchendpoints, **store_config)

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
                         metadata_context=None, context_resolver=self.service.resolve_context, na=nan)

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

    def _upload_many(self, paths: List[Path], content_type: str) -> List[Dict]:

        async def _bulk():
            loop = asyncio.get_event_loop()
            semaphore = Semaphore(self.service.max_connection)
            async with ClientSession(headers=self.service.headers_upload) as session:
                tasks = (_create_task(x, loop, semaphore, session) for x in paths)
                return await asyncio.gather(*tasks)

        def _create_task(path, loop, semaphore, session):
            default = "application/octet-stream"
            mime_type = (content_type or mimetypes.guess_type(str(path))[0] or default)
            # FIXME Nexus seems to not parse the Content-Disposition 'filename*' field  properly.
            # data = FormData()
            # data.add_field("file", path.open("rb"), content_type=mime_type, filename=path.name)
            # FIXME This hack is to prevent sending Content-Disposition with the 'filename*' field.
            data = MultipartWriter("form-data")
            part = data.append(path.open("rb"))
            part.headers[CONTENT_TYPE] = mime_type
            part.headers[CONTENT_DISPOSITION] = f'form-data; name="file"; filename="{path.name}"'
            return loop.create_task(_upload(data, semaphore, session))

        async def _upload(data, semaphore, session):
            async with semaphore:
                async with session.post(self.service.url_files, data=data) as response:
                    body = await response.json()
                    if response.status < 400:
                        return body
                    else:
                        msg = " ".join(re.findall('[A-Z][^A-Z]*', body["@type"])).lower()
                        raise UploadingError(msg)

        return asyncio.run(_bulk())

    def _upload_one(self, path: Path, content_type: str) -> Dict:
        file = str(path.absolute())
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

    def retrieve(self, id: str, version: Optional[Union[int, str]],
                 cross_bucket: bool) -> Resource:

        parsed_id = urlparse(id)
        id_without_query = f"{parsed_id.scheme}://{parsed_id.netloc}{parsed_id.path}"
        params = None
        if version is not None:
            if isinstance(version, int):
                params = {"rev": version}
            elif isinstance(version, str):
                params = {"tag": version}
            else:
                raise RetrievalError("incorrect 'version'")
        if parsed_id.query is not None:
            query_params = parse_qs(parsed_id.query)
            if params is not None:
                query_params.update(params)
            params = query_params
        url_base = self.service.url_resolver if cross_bucket else self.service.url_resources
        url = "/".join((url_base, "_", quote_plus(id_without_query)))
        try:
            response = requests.get(url, params=params, headers=self.service.headers)
            response.raise_for_status()
        except HTTPError as e:
            raise RetrievalError(_error_message(e))
        else:
            data = response.json()
            resource = self.service.to_resource(data)
            resource._synchronized = True
            self.service.sync_metadata(resource, data)
            return resource

    def _retrieve_filename(self, id: str) -> str:
        try:
            response = requests.get(id, headers=self.service.headers)
            response.raise_for_status()
            metadata = response.json()
            return metadata["_filename"]
        except HTTPError as e:
            raise DownloadingError(_error_message(e))

    def _download_many(self, urls: List[str], paths: List[str], store_metadata: Optional[DictWrapper], cross_bucket: bool) -> None:

        async def _bulk():
            loop = asyncio.get_event_loop()
            semaphore = Semaphore(self.service.max_connection)
            async with ClientSession(headers=self.service.headers_download) as session:
                tasks = (_create_task(x, y, z, loop, semaphore, session) for x, y, z in zip(urls, paths, store_metadata))
                return await asyncio.gather(*tasks)

        def _create_task(url, path, store_metadata, loop, semaphore, session):
            return loop.create_task(_download(url, path, store_metadata, semaphore, session))

        async def _download(url, path, store_metadata, semaphore, session):
            async with semaphore:
                url_base, org, project = self._prepare_download_one(url, path, store_metadata, cross_bucket)
                async with session.get(url_base) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        raise DownloadingError(f"Downloading from {org}/{project}:{_error_message(e)}")
                    else:
                        with open(path, "wb") as f:
                            data = await response.read()
                            f.write(data)

        return asyncio.run(_bulk())

    def _download_one(self, url: str, path: str, store_metadata: Optional[DictWrapper], cross_bucket: bool) -> None:
        try:
            url_base, org, project = self._prepare_download_one(url, path, store_metadata, cross_bucket)
            response = requests.get(url=url_base, headers=self.service.headers_download)
            response.raise_for_status()
        except Exception as e:
            raise DownloadingError(f"Downloading from {org}/{project}:{_error_message(e)}")
        else:
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=4096):
                    f.write(chunk)

    def _prepare_download_one(self, url: str, path: str, store_metadata: Optional[DictWrapper], cross_bucket: bool) -> Tuple[str,str,str]:
        # this is a hack since _self and _id have the same uuid
        file_id = url.split("/")[-1]
        file_id = unquote(file_id)
        if file_id.startswith("http"):
            file_id = file_id.split("/")[-1]
        if len(file_id) < 1:
            raise DownloadingError("Invalid file name")
        if cross_bucket:
            if store_metadata is not None:
                project = store_metadata._project.split('/')[-1]
                org = store_metadata._project.split('/')[-2]
            else:
                raise ValueError(f"Downloading non registered file is not allowed when cross_bucket is set to {cross_bucket}")
        else:
            org = self.service.organisation
            project = self.service.project

        url_base = "/".join((self.service.url_base_files, quote_plus(org), quote_plus(project), quote_plus(file_id)))
        return url_base, org, project

    # CR[U]D.

    def update(self, data: Union[Resource, List[Resource]], schema_id: str) -> None:
        run(self._update_one, self._update_many, data, id_required=True, required_synchronized=False,
            execute_actions=True, exception=UpdatingError, monitored_status="_synchronized", schema_id=schema_id)

    def _update_many(self, resources: List[Resource], schema_id: str) -> None:
        update_callback = self.service.default_callback(self._update_many.__name__)
        verified = self.service.verify(
            resources, self._update_many.__name__, UpdatingError, id_required=True,
            required_synchronized=False, execute_actions=True)
        self.service.batch_request(verified, BatchAction.UPDATE, update_callback, UpdatingError)

    def _update_one(self, resource: Resource, schema_id: str) -> None:
        context = self.model_context or self.context
        data = as_jsonld(resource, "compacted", False, model_context=context, metadata_context=None,
                         context_resolver=self.service.resolve_context, na=nan)
        rev = {"rev": resource._store_metadata._rev}
        schema = quote_plus(schema_id) if schema_id else "_"
        url = f"{self.service.url_resources}/{schema}/{quote_plus(resource.id)}"
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
        cross_bucket = params.get("cross_bucket", False)
        bucket = params.get("bucket",None)
        search_in_graph = params.get("search_in_graph", True)
        distinct = params.get("distinct", False)
        project_statements = ''
        if bucket and not cross_bucket:
            not_supported(("bucket", True))
        elif bucket:
            project_statements = f"Filter (?project = <{'/'.join([self.endpoint,'projects',bucket])}>)"
        elif not cross_bucket:
            project_statements = f"Filter (?project = <{'/'.join([self.endpoint,'projects',self.organisation, self.project])}>)"

        if filters and isinstance(filters[0], dict):
            filters = create_filters_from_dict(filters[0])
        query_statements, query_filters = build_query_statements(self.model_context, filters)
        query_statements.insert(0, f"<{self.service.project_property}> ?project")
        query_statements.insert(1, f"<{self.service.deprecated_property}> {format_type[CategoryDataType.BOOLEAN](deprecated)}")
        statements = "\n".join((";\n ".join(query_statements), ".\n ".join(query_filters)))
        query = _create_select_query(f"?id {statements} {project_statements}", distinct, search_in_graph)

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
                self.service.sparql_endpoint["endpoint"], data=query, headers=self.service.headers_sparql)
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

    def _elastic(self, query: str, limit: int, offset: int = None) -> List[Resource]:
        try:

            print(query)
            response = requests.post(
                self.service.elastic_endpoint["endpoint"], data=query, headers=self.service.headers_elastic)
            response.raise_for_status()
        except Exception as e:
            print(e)
            raise QueryingError(e)
        else:
            results = response.json()
            return [Resource(**{k: v for k, v in hit.items()}) for hit in results["hits"]['hits']]

    # Utils.

    def _initialize_service(self, endpoint: Optional[str], bucket: Optional[str],
                            token: Optional[str], searchendpoints:Optional[Dict], **store_config) -> Any:
        try:
            self.organisation, self.project = self.bucket.split('/')
            max_connection = store_config.pop("max_connection", 50)
            if max_connection <=0:
                raise ValueError(f"max_connection value should be great than 0 but {max_connection} is provided")
            store_context_config = store_config.pop("vocabulary", {})
            nexus_context_iri = store_context_config.get("iri", Service.NEXUS_CONTEXT_FALLBACK)
            namespace = store_context_config.get("namespace", Service.NEXUS_NAMESPACE_FALLBACK)
            project_property = store_context_config.get("project_property", Service.PROJECT_PROPERTY_FALLBACK)
            deprecated_property = store_context_config.get("deprecated_property", Service.DEPRECATED_PROPERTY_FALLBACK)
            content_type = store_config.pop("Content-Type", "application/ld+json")
            accept = store_config.pop("Accept", "application/ld+json")
            files_upload_config = store_config.pop("files_upload", {"Accept":"application/ld+json"})
            files_download_config = store_config.pop("files_download", {"Accept":"*/*"})
        except Exception as ve:
            raise ValueError(f"Store configuration error: {ve}")
        else:
            return Service(endpoint=endpoint, org=self.organisation, prj=self.project, token=token,
                           model_context=self.model_context, max_connection=max_connection, searchendpoints=searchendpoints,
                           store_context=nexus_context_iri, namespace=namespace, project_property = project_property,
                           deprecated_property=deprecated_property, content_type=content_type, accept=accept,
                           files_upload_config=files_upload_config, files_download_config=files_download_config)


def _error_message(error: HTTPError) -> str:

    def format_message(msg):
        return "".join([msg[0].lower(), msg[1:-1], msg[-1] if msg[-1] != "." else ""])

    try:
        error_json = error.response.json()
        if "reason" in error_json:
            return format_message(error_json["reason"])
    except AttributeError as e:
        pass
    try:
        return format_message(error.response.text())
    except Exception:
        return format_message(str(error))


def build_query_statements(context: Context, *conditions) -> Tuple[List,List]:
    statements = list()
    filters = list()
    for index, f in enumerate(*conditions):
        try:
            last_term = context.terms[f.path[-1]]
        except KeyError:
            last_term = None
        if f.path[-1] == "id":
            property_path = "/".join(f.path[:-1])
        else:
            property_path = "/".join(f.path)
        if f.path[-1] == "type" or f.path[-1] == "id" or (last_term is not None and last_term.type == "@id"):
            if f.operator == "__eq__":
                statements.append(f"{property_path} {_box_value_as_full_iri(f.value)}")
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
                filters.append(f"FILTER(?v{index} = {_box_value_as_full_iri(value)})")
            else:
                statements.append(f"{property_path} ?v{index}")
                filters.append(f"FILTER(?v{index} {operator_map[f.operator]} {_box_value_as_full_iri(value)})")

    return statements, filters


def _box_value_as_full_iri(value):
    return f"<{value}>" if is_valid_url(value) else value


def _create_select_query(statements, distinct, search_in_graph):
    where_clauses = f"{{ Graph ?g {{{statements}}}}}" if search_in_graph else \
        f"{{{statements}}}"
    select_vars = "DISTINCT ?id ?project" if distinct else "?id ?project"
    return f"SELECT {select_vars} WHERE {where_clauses}"