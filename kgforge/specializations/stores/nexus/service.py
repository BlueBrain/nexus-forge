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
import copy
import json
import re
from asyncio import Task
from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Callable, Dict, List, Optional, Union
from urllib.error import URLError
from urllib.parse import quote_plus, urlparse

import nest_asyncio
import nexussdk as nexus
import requests
from aiohttp import ClientSession, hdrs
from numpy import nan
from requests import HTTPError

from kgforge.core import Resource
from kgforge.core.commons.actions import (
    Action,
    collect_lazy_actions,
    execute_lazy_actions,
    LazyAction,
)
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import (
    _from_jsonld_one,
    _remove_ld_keys,
    as_jsonld,
    recursive_resolve,
)
from kgforge.core.wrappings.dict import wrap_dict


class BatchAction(Enum):
    CREATE = "create"
    FETCH = "fetch"
    DEPRECATE = "deprecate"
    UPDATE = "update"
    TAG = "tag"
    UPLOAD = "upload"
    DOWNLOAD = "download"


BatchResult = namedtuple("BatchResult", ["resource", "response"])
BatchResults = List[BatchResult]


class Service:

    NEXUS_NAMESPACE_FALLBACK = "https://bluebrain.github.io/nexus/vocabulary/"
    NEXUS_CONTEXT_FALLBACK = "https://bluebrain.github.io/nexus/contexts/resource.json"
    NEXUS_CONTEXT_SOURCE_FALLBACK = (
        "https%3A%2F%2Fbluebrain.github.io%2Fnexus%2Fcontexts%2Fresource.json/source"
    )
    DEFAULT_SPARQL_INDEX_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}defaultSparqlIndex"
    DEFAULT_ES_INDEX_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}defaultElasticSearchIndex"
    DEPRECATED_PROPERTY_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}deprecated"
    PROJECT_PROPERTY_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}project"

    def __init__(
        self,
        endpoint: str,
        org: str,
        prj: str,
        token: str,
        model_context: Context,
        max_connection: int,
        searchendpoints: Dict,
        store_context: str,
        store_local_context: str,
        namespace: str,
        project_property: str,
        deprecated_property: bool,
        content_type: str,
        accept: str,
        files_upload_config: Dict,
        files_download_config: Dict,
        **params,
    ):

        nexus.config.set_environment(endpoint)
        self.endpoint = endpoint
        self.organisation = org
        self.project = prj
        self.model_context = model_context
        self.context_cache: Dict = dict()
        self.max_connection = max_connection
        self.params = copy.deepcopy(params)
        self.store_context = store_context
        self.store_local_context = store_local_context
        self.namespace = namespace
        self.project_property = project_property
        self.deprecated_property = deprecated_property
        self.default_sparql_index = f"{self.namespace}defaultSparqlIndex"
        self.default_es_index = f"{self.namespace}defaultElasticSearchIndex"

        self.headers = {"Content-Type": content_type, "Accept": accept}

        sparql_config = (
            searchendpoints["sparql"]
            if searchendpoints and "sparql" in searchendpoints
            else None
        )
        elastic_config = (
            searchendpoints["elastic"]
            if searchendpoints and "elastic" in searchendpoints
            else None
        )

        self.headers_sparql = {
            "Content-Type": sparql_config["Content-Type"]
            if sparql_config and "Content-Type" in sparql_config
            else "text/plain",
            "Accept": sparql_config["Accept"]
            if sparql_config and "Accept" in sparql_config
            else "application/sparql-results+json",
        }
        self.headers_elastic = {
            "Content-Type": elastic_config["Content-Type"]
            if elastic_config and "Content-Type" in elastic_config
            else "application/json",
            "Accept": elastic_config["Accept"]
            if elastic_config and "Accept" in elastic_config
            else "application/json",
        }
        self.headers_upload = {
            "Accept": files_upload_config.pop("Accept"),
        }
        self.headers_download = {"Accept": files_download_config.pop("Accept")}

        if token is not None:
            nexus.config.set_token(token)
            self.headers["Authorization"] = "Bearer " + token
            self.headers_sparql["Authorization"] = "Bearer " + token
            self.headers_elastic["Authorization"] = "Bearer " + token
            self.headers_upload["Authorization"] = "Bearer " + token
            self.headers_download["Authorization"] = "Bearer " + token
        self.context = Context(self.get_project_context())

        self.url_base_files = "/".join((self.endpoint, "files"))
        self.url_files = "/".join(
            (self.url_base_files, quote_plus(org), quote_plus(prj))
        )
        self.url_resources = "/".join(
            (self.endpoint, "resources", quote_plus(org), quote_plus(prj))
        )
        self.url_resolver = "/".join(
            (self.endpoint, "resolvers", quote_plus(org), quote_plus(prj))
        )
        self.metadata_context = Context(
            recursive_resolve(
                self.store_context, self.resolve_context, already_loaded=[]
            ),
            store_context,
        )
        sparql_view = (
            sparql_config["endpoint"]
            if sparql_config and "endpoint" in sparql_config
            else self.default_sparql_index
        )
        elastic_view = (
            elastic_config["endpoint"]
            if elastic_config and "endpoint" in elastic_config
            else self.default_es_index
        )
        default_str_keyword_field = (
            elastic_config["default_str_keyword_field"]
            if elastic_config and "default_str_keyword_field" in elastic_config
            else None
        )

        es_mapping = (
            elastic_config["mapping"]
            if elastic_config and "mapping" in elastic_config
            else None
        )

        self.sparql_endpoint = dict()
        self.elastic_endpoint = dict()
        self.sparql_endpoint["endpoint"] = "/".join(
            (
                self.endpoint,
                "views",
                quote_plus(org),
                quote_plus(prj),
                quote_plus(sparql_view),
                "sparql",
            )
        )
        self.sparql_endpoint["type"] = "sparql"

        self.elastic_endpoint["endpoint"] = "/".join(
            (
                self.endpoint,
                "views",
                quote_plus(org),
                quote_plus(prj),
                quote_plus(elastic_view),
                "_search",
            )
        )
        self.elastic_endpoint["type"] = "elastic"
        self.elastic_endpoint["view"] = LazyAction(
            nexus.views.fetch,
            quote_plus(org),
            quote_plus(prj),
            es_mapping
            if es_mapping
            else elastic_view,  # Todo consider using Dict for es_mapping
        )
        self.elastic_endpoint["default_str_keyword_field"] = default_str_keyword_field

        # The following code is for async to work on jupyter notebooks
        try:
            asyncio.get_event_loop()
            nest_asyncio.apply()
        except RuntimeError:
            pass

    def get_project_context(self) -> Dict:
        project_data = nexus.projects.fetch(self.organisation, self.project)
        context = {"@base": project_data["base"], "@vocab": project_data["vocab"]}
        return context

    def resolve_context(self, iri: str, local_only: Optional[bool] = False) -> Dict:
        if iri in self.context_cache:
            return self.context_cache[iri]
        try:
            context_to_resolve = (
                self.store_local_context if iri == self.store_context else iri
            )
            url = "/".join((self.url_resolver, "_", quote_plus(context_to_resolve)))
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            resource = response.json()
        except Exception as e:
            if local_only is False:
                try:
                    context = Context(context_to_resolve)
                except URLError:
                    raise ValueError(f"{context_to_resolve} is not resolvable")
                else:
                    document = context.document["@context"]
            else:
                raise ValueError(f"{context_to_resolve} is not resolvable")
        else:
            document = json.loads(json.dumps(resource["@context"]))
        if isinstance(document, list):
            if self.store_context in document:
                document.remove(self.store_context)
            if self.store_local_context in document:
                document.remove(self.store_local_context)
        self.context_cache.update({context_to_resolve: document})
        return document

    def batch_request(
        self,
        resources: List[Resource],
        action: BatchAction,
        callback: Callable,
        error_type: Callable,
        **kwargs,
    ) -> (BatchResults, BatchResults):
        def create_tasks(
            semaphore, session, loop, data, batch_action, f_callback, error
        ):
            futures = []
            schema_id = kwargs.get("schema_id")
            schema_id = "_" if schema_id is None else quote_plus(schema_id)
            for resource in data:
                params = deepcopy(kwargs.get("params", {}))
                if batch_action == batch_action.CREATE:
                    context = self.model_context or self.context
                    payload = as_jsonld(
                        resource,
                        "compacted",
                        False,
                        model_context=context,
                        metadata_context=None,
                        context_resolver=self.resolve_context,
                        na=nan,
                    )
                    url = f"{self.url_resources}/{schema_id}"
                    prepared_request = loop.create_task(
                        queue(
                            hdrs.METH_POST,
                            semaphore,
                            session,
                            url,
                            resource,
                            error,
                            payload,
                            params,
                        )
                    )

                if batch_action == batch_action.UPDATE:
                    url = "/".join(
                        (self.url_resources, schema_id, quote_plus(resource.id))
                    )
                    params["rev"] = resource._store_metadata._rev

                    payload = as_jsonld(
                        resource,
                        "compacted",
                        False,
                        model_context=self.model_context,
                        metadata_context=None,
                        context_resolver=self.resolve_context,
                        na=nan,
                    )
                    prepared_request = loop.create_task(
                        queue(
                            hdrs.METH_PUT,
                            semaphore,
                            session,
                            url,
                            resource,
                            error,
                            payload,
                            params,
                        )
                    )

                if batch_action == batch_action.TAG:
                    url = "/".join(
                        (self.url_resources, "_", quote_plus(resource.id), "tags")
                    )
                    rev = resource._store_metadata._rev
                    params["rev"] = rev
                    payload = {"tag": kwargs.get("tag"), "rev": rev}
                    prepared_request = loop.create_task(
                        queue(
                            hdrs.METH_POST,
                            semaphore,
                            session,
                            url,
                            resource,
                            error,
                            payload,
                            params,
                        )
                    )

                if batch_action == batch_action.DEPRECATE:
                    url = "/".join((self.url_resources, "_", quote_plus(resource.id)))
                    params["rev"] = resource._store_metadata._rev
                    prepared_request = loop.create_task(
                        queue(
                            hdrs.METH_DELETE,
                            semaphore,
                            session,
                            url,
                            resource,
                            error,
                            params=params,
                        )
                    )

                if batch_action == BatchAction.FETCH:
                    resource_org, resource_prj = resource.project.split("/")[-2:]
                    resource_url = "/".join(
                        (
                            self.endpoint,
                            "resources",
                            quote_plus(resource_org),
                            quote_plus(resource_prj),
                        )
                    )
                    url = "/".join((resource_url, "_", quote_plus(resource.id)))
                    prepared_request = loop.create_task(
                        queue(hdrs.METH_GET, semaphore, session, url, resource, error)
                    )

                if f_callback:
                    prepared_request.add_done_callback(f_callback)
                futures.append(prepared_request)
            return futures

        async def queue(
            method,
            semaphore,
            session,
            url,
            resource,
            exception,
            payload=None,
            params=None,
        ):
            async with semaphore:
                return await request(
                    method, session, url, resource, payload, params, exception
                )

        async def request(method, session, url, resource, payload, params, exception):
            async with session.request(
                method,
                url,
                headers=self.headers,
                data=json.dumps(payload),
                params=params,
            ) as response:
                content = await response.json()
                if response.status < 400:
                    return BatchResult(resource, content)
                else:
                    msg = " ".join(re.findall("[A-Z][^A-Z]*", content["@type"])).lower()
                    error = exception(msg)
                    return BatchResult(resource, error)

        async def dispatch_action():
            semaphore = asyncio.Semaphore(self.max_connection)
            loop = asyncio.get_event_loop()
            async with ClientSession() as session:
                tasks = create_tasks(
                    semaphore, session, loop, resources, action, callback, error_type
                )
                return await asyncio.gather(*tasks)

        return asyncio.run(dispatch_action())

    def sync_metadata(self, resource: Resource, result: Dict) -> None:
        metadata = (
            {"id": resource.id}
            if hasattr(resource, "id")
            else (
                {"id": resource.__getattribute__("@id")}
                if hasattr(resource, "@id")
                else dict()
            )
        )
        keys = sorted(self.metadata_context.terms.keys())
        keys.extend(["_index", "_score"])
        only_meta = {k: v for k, v in result.items() if k in keys}
        metadata.update(_remove_ld_keys(only_meta, self.metadata_context, False))
        resource._store_metadata = wrap_dict(metadata)

    def synchronize_resource(
        self,
        resource: Resource,
        response: Union[Exception, Dict],
        action_name: str,
        succeeded: bool,
        synchronized: bool,
    ) -> None:
        if succeeded:
            action = Action(action_name, succeeded, None)
            self.sync_metadata(resource, response)
        else:
            action = Action(action_name, succeeded, response)
        resource._last_action = action
        resource._synchronized = synchronized

    def default_callback(self, fun_name: str) -> Callable:
        def callback(task: Task):
            result = task.result()
            if isinstance(result.response, Exception):
                self.synchronize_resource(
                    result.resource, result.response, fun_name, False, False
                )
            else:
                self.synchronize_resource(
                    result.resource, result.response, fun_name, True, True
                )

        return callback

    def verify(
        self,
        resources: List[Resource],
        function_name,
        exception: Callable,
        id_required: bool,
        required_synchronized: bool,
        execute_actions: bool,
    ) -> List[Resource]:
        valid = list()
        for resource in resources:
            if id_required and not hasattr(resource, "id"):
                error = exception("resource should have an id")
                self.synchronize_resource(resource, error, function_name, False, False)
                continue
            if required_synchronized is not None:
                synchronized = resource._synchronized
                if synchronized is not required_synchronized:
                    be_or_not_be = "be" if required_synchronized is True else "not be"
                    error = exception(f"resource should {be_or_not_be} synchronized")
                    self.synchronize_resource(
                        resource, error, function_name, False, False
                    )
                    continue
            if execute_actions:
                lazy_actions = collect_lazy_actions(resource)
                if lazy_actions is not None:
                    try:
                        execute_lazy_actions(resource, lazy_actions)
                    except Exception as e:
                        self.synchronize_resource(
                            resource, exception(e), function_name, False, False
                        )
                        continue
            valid.append(resource)
        return valid

    def to_resource(
        self, payload: Dict, sync_metadata: bool = True, **kwargs
    ) -> Resource:
        data_context = deepcopy(payload.get("@context", None))
        if not isinstance(data_context, list):
            data_context = [data_context]
        if self.store_context in data_context:
            data_context.remove(self.store_context)
        if self.store_local_context in data_context:
            data_context.remove(self.store_local_context)
        data_context = data_context[0] if len(data_context) == 1 else data_context
        metadata = dict()
        data = dict()
        for k, v in payload.items():
            if k in self.metadata_context.terms.keys():
                metadata[k] = v
            else:
                data[k] = v

        if (
            self.model_context
            and data_context is not None
            and data_context == self.model_context.iri
        ):
            resolved_ctx = self.model_context.document["@context"]
        elif data_context is not None:
            resolved_ctx = recursive_resolve(
                data_context,
                self.resolve_context,
                already_loaded=[self.store_local_context, self.store_context],
            )
        else:
            resolved_ctx = None
        if resolved_ctx:
            data["@context"] = resolved_ctx
            resource = _from_jsonld_one(data)
            resource.context = data_context
        else:
            resource = Resource.from_json(data)

        if len(metadata) > 0 and sync_metadata:
            metadata.update(kwargs)
            self.sync_metadata(resource, metadata)
        return resource
