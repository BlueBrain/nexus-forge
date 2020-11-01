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
import re
from asyncio import Task
from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Callable, Dict, List, Optional, Union
from urllib.error import URLError
from urllib.parse import quote_plus

import nest_asyncio
import nexussdk as nexus
from aiohttp import ClientSession, hdrs

from kgforge.core import Resource
from kgforge.core.commons.actions import Action, collect_lazy_actions, execute_lazy_actions
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import (_from_jsonld_one, _remove_ld_keys, as_jsonld,
                                          recursive_resolve)
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

NEXUS_NAMESPACE = "https://bluebrain.github.io/nexus/vocabulary/"
NEXUS_CONTEXT = "https://bluebrain.github.io/nexus/contexts/resource.json"
DEPRECATED_PROPERTY = f"{NEXUS_NAMESPACE}deprecated"
PROJECT_PROPERTY = f"{NEXUS_NAMESPACE}project"


class Service:

    def __init__(self, endpoint: str, org: str, prj: str, token: str, model_context: Context,
                 max_connections: int, searchendpoints: Dict):

        nexus.config.set_environment(endpoint)
        nexus.config.set_token(token)
        self.endpoint = endpoint
        self.organisation = org
        self.project = prj
        self.model_context = model_context
        self.context = Context(self.get_project_context())
        self.context_cache: Dict = dict()
        self.metadata_context = Context(self.resolve_context(NEXUS_CONTEXT), NEXUS_CONTEXT)
        self.max_connections = max_connections
        self.headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/ld+json",
            "Accept": "application/ld+json"
        }
        self.headers_sparql = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/sparql-query",
            "Accept": "application/ld+json"
        }
        self.headers_upload = {
            "Authorization": "Bearer " + token,
            "Accept": "application/ld+json",
        }
        self.headers_download = {
            "Authorization": "Bearer " + token,
            "Accept": "*/*"
        }
        self.url_resources = "/".join((self.endpoint, "resources", quote_plus(org), quote_plus(prj)))
        self.url_files = "/".join((self.endpoint, "files", quote_plus(org), quote_plus(prj)))

        sparql_view = searchendpoints['sparql']['endpoint'] if searchendpoints and "sparql" in searchendpoints else "nxv:defaultSparqlIndex"

        self.sparql_endpoint = "/".join((self.endpoint, "views", quote_plus(org), quote_plus(prj),quote_plus(sparql_view), "sparql"))
        # The following code is for async to work on jupyter notebooks
        try:
            asyncio.get_event_loop()
            nest_asyncio.apply()
        except RuntimeError:
            pass

    def get_project_context(self) -> Dict:
        project_data = nexus.projects.fetch(self.organisation, self.project)
        context = {
            "@base": project_data["base"],
            "@vocab": project_data["vocab"]
        }
        return context

    def resolve_context(self, iri: str, local_only: Optional[bool] = False) -> Dict:
        if iri in self.context_cache:
            return self.context_cache[iri]
        try:
            resource = nexus.resources.fetch(self.organisation, self.project, iri)
        except nexus.HTTPError:
            if local_only is False:
                try:
                    context = Context(iri)
                except URLError:
                    raise ValueError(f"{iri} is not resolvable")
                else:
                    document = context.document["@context"]
            else:
                raise ValueError(f"{iri} is not resolvable")
        else:
            document = json.loads(json.dumps(resource["@context"]))
        self.context_cache.update({iri: document})
        return document

    def batch_request(self, resources: List[Resource], action: BatchAction, callback: Callable,
                      error_type: Callable, **kwargs) -> (BatchResults, BatchResults):

        def create_tasks(semaphore, session, loop, data, batch_action, f_callback, error):
            futures = []
            for resource in data:
                if batch_action == batch_action.CREATE:
                    context = self.model_context or self.context
                    payload = as_jsonld(resource, "compacted", False,
                                        model_context=context, metadata_context=None,
                                        context_resolver=self.resolve_context)
                    schema_id = kwargs.get("schema_id")
                    schema_id = "_" if schema_id is None else quote_plus(schema_id)
                    url = f"{self.url_resources}/{schema_id}"
                    prepared_request = loop.create_task(
                        queue(hdrs.METH_POST, semaphore, session, url, resource, error, payload))

                if batch_action == batch_action.UPDATE:
                    url = "/".join((self.url_resources, "_", quote_plus(resource.id)))
                    params = {"rev": resource._store_metadata._rev}
                    payload = as_jsonld(resource, "compacted", False,
                                        model_context=self.model_context,
                                        metadata_context=None,
                                        context_resolver=self.resolve_context)
                    prepared_request = loop.create_task(
                        queue(hdrs.METH_PUT, semaphore, session, url, resource, error, payload,
                              params))

                if batch_action == batch_action.TAG:
                    url = "/".join((self.url_resources, "_", quote_plus(resource.id), "tags"))
                    rev = resource._store_metadata._rev
                    params = {"rev": rev}
                    payload = {"tag": kwargs.get("tag"), "rev": rev}
                    prepared_request = loop.create_task(
                        queue(hdrs.METH_POST, semaphore, session, url, resource, error, payload,
                              params))

                if batch_action == batch_action.DEPRECATE:
                    url = "/".join((self.url_resources, "_", quote_plus(resource.id)))
                    params = {"rev": resource._store_metadata._rev}
                    prepared_request = loop.create_task(
                        queue(hdrs.METH_DELETE, semaphore, session, url, resource, error,
                              params=params))

                if batch_action == BatchAction.FETCH:

                    resource_org, resource_prj  = resource.project.split("/")[-2:]
                    resource_url = "/".join((self.endpoint, "resources", quote_plus(resource_org), quote_plus(resource_prj)))
                    url = "/".join((resource_url, "_", quote_plus(resource.id)))
                    prepared_request = loop.create_task(
                        queue(hdrs.METH_GET, semaphore, session, url, resource, error))

                if f_callback:
                    prepared_request.add_done_callback(f_callback)
                futures.append(prepared_request)
            return futures

        async def queue(method, semaphore, session, url, resource, exception, payload=None,
                        params=None):
            async with semaphore:
                return await request(method, session, url, resource, payload, params, exception)

        async def request(method, session, url, resource, payload, params, exception):
            async with session.request(method, url, headers=self.headers,
                                       data=json.dumps(payload), params=params) as response:
                content = await response.json()
                if response.status < 400:
                    return BatchResult(resource, content)
                else:
                    msg = " ".join(re.findall('[A-Z][^A-Z]*', content["@type"])).lower()
                    error = exception(msg)
                    return BatchResult(resource, error)

        async def dispatch_action():
            semaphore = asyncio.Semaphore(self.max_connections)
            loop = asyncio.get_event_loop()
            async with ClientSession() as session:
                tasks = create_tasks(semaphore, session, loop, resources, action, callback, error_type)
                return await asyncio.gather(*tasks)

        return asyncio.run(dispatch_action())

    def sync_metadata(self, resource: Resource, result: Dict) -> None:
        metadata = {"id": resource.id}
        keys = sorted(self.metadata_context.terms.keys())
        only_meta = {k: v for k, v in result.items() if k in keys}
        metadata.update(_remove_ld_keys(only_meta, self.metadata_context, False))
        resource._store_metadata = wrap_dict(metadata)

    def synchronize_resource(self, resource: Resource, response: Union[Exception, Dict],
                             action_name: str, succeeded: bool, synchronized: bool) -> None:
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
                    result.resource, result.response, fun_name, False, False)
            else:
                self.synchronize_resource(
                    result.resource, result.response, fun_name, True, True)
        return callback

    def verify(self, resources: List[Resource], function_name, exception: Callable,
               id_required: bool, required_synchronized: bool, execute_actions: bool) -> List[Resource]:
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
                    self.synchronize_resource(resource, error, function_name, False, False)
                    continue
            if execute_actions:
                lazy_actions = collect_lazy_actions(resource)
                if lazy_actions is not None:
                    try:
                        execute_lazy_actions(resource, lazy_actions)
                    except Exception as e:
                        self.synchronize_resource(
                            resource, exception(e), function_name, False, False)
                        continue
            valid.append(resource)
        return valid

    def to_resource(self, payload: Dict) -> Resource:
        data_context = deepcopy(payload["@context"])
        if not isinstance(data_context, list):
            data_context = [data_context]
        if NEXUS_CONTEXT in data_context:
            data_context.remove(NEXUS_CONTEXT)
        data_context = data_context[0] if len(data_context) == 1 else data_context
        metadata = dict()
        data = dict()
        for k, v in payload.items():
            if k in self.metadata_context.terms.keys():
                metadata[k] = v
            else:
                data[k] = v

        if self.model_context and data_context == self.model_context.iri:
            resolved_ctx = self.model_context.document["@context"]
        else:
            resolved_ctx = recursive_resolve(data_context, self.resolve_context)
        data["@context"] = resolved_ctx
        resource = _from_jsonld_one(data)
        resource.context = data_context
        if len(metadata) > 0:
            self.sync_metadata(resource, metadata)
        return resource
