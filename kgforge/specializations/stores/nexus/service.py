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

import asyncio
import json
import re
from asyncio import Task
from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Dict, List, Callable, Union
from urllib.error import URLError
from urllib.parse import quote_plus

import nest_asyncio
import nexussdk as nexus
from aiohttp import ClientSession, hdrs

from kgforge.core import Resource
from kgforge.core.commons.actions import Action, collect_lazy_actions, execute_lazy_actions
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import as_jsonld, _from_jsonld_one, _remove_ld_keys
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


class Service:

    def __init__(self, endpoint: str, org: str, prj: str, token: str, model_context: Context,
                 max_connections: int):

        nexus.config.set_environment(endpoint)
        nexus.config.set_token(token)
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
        self.url_resources = '/'.join((endpoint, 'resources', quote_plus(org), quote_plus(prj)))
        self.url_files = '/'.join((endpoint, 'files', quote_plus(org), quote_plus(prj)))
        # This async to work on jupyter notebooks
        nest_asyncio.apply()

    def get_project_context(self) -> Dict:
        project_data = nexus.projects.fetch(self.organisation, self.project)
        context = {
            "@base": project_data["base"],
            "@vocab": project_data["vocab"]
        }
        return context

    def resolve_context(self, iri: str) -> Dict:
        if iri in self.context_cache:
            return self.context_cache[iri]
        try:
            resource = nexus.resources.fetch(self.organisation, self.project, iri)
        except nexus.HTTPError:
            try:
                context = Context(iri)
            except URLError:
                raise ValueError(f"{iri} is not resolvable")
            else:
                document = context.document["@context"]
        else:
            document = json.loads(json.dumps(resource["@context"]))
        self.context_cache.update({iri: document})
        return document

    def batch_request(self, resources: List[Resource], action: BatchAction, callback: Callable,
                      error_type: Callable, **kwargs) -> (BatchResults, BatchResults):

        def create_tasks(semaphore, session, data, batch_action, f_callback, error):
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
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_POST, semaphore, session, url, resource, 201, error,
                              payload=payload))

                if batch_action == batch_action.UPDATE:
                    url = "/".join((self.url_resources, "_", quote_plus(resource.id)))
                    params = {"rev": resource._store_metadata._rev}
                    payload = as_jsonld(resource, "compacted", False,
                                        model_context=self.model_context,
                                        metadata_context=None,
                                        context_resolver=self.resolve_context)
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_PUT, semaphore, session, url, resource, 200, error,
                              payload=payload, params=params))

                if batch_action == batch_action.TAG:
                    url = "/".join((self.url_resources, "_", quote_plus(resource.id), "tags"))
                    rev = resource._store_metadata._rev
                    params = {"rev": rev}
                    payload = {"tag": kwargs.get("tag"), "rev": rev}
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_POST, semaphore, session, url, resource, 201, error,
                              payload=payload, params=params))

                if batch_action == batch_action.DEPRECATE:
                    url = "/".join((self.url_resources, "_", quote_plus(resource.id)))
                    params = {"rev": resource._store_metadata._rev}
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_DELETE, semaphore, session, url, resource, 200, error,
                              params=params))

                if batch_action == BatchAction.FETCH:
                    try:
                        identifier = resource.id
                    except AttributeError:
                        identifier = resource
                    url = "/".join((self.url_resources, "_", quote_plus(identifier)))
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_GET, semaphore, session, url, resource, 200, error))

                prepared_request.add_done_callback(f_callback)
                futures.append(prepared_request)
            return futures

        async def queue(method, semaphore, session, url, resource, success_code, exception,
                        payload=None, params=None):
            async with semaphore:
                return await request(method, session, url, resource, payload, params, success_code,
                                     exception)

        async def request(method, session, url, resource, payload, params, success_code, exception):
            try:
                async with session.request(method, url, headers=self.headers,
                                           data=json.dumps(payload), params=params) as response:
                    content = await response.json()
                    if response.status == success_code:
                        if method is hdrs.METH_GET:
                            resource = self.to_resource(content)
                        return BatchResult(resource, content)
                    else:
                        if method is hdrs.METH_GET:
                            resource = Resource(id=resource)
                        msg = " ".join(re.findall('[A-Z][^A-Z]*', content["@type"])).lower()
                        error = exception(msg)
                        return BatchResult(resource, error)
            except Exception as e:
                return BatchResult(resource, exception(e))

        async def dispatch_action():
            semaphore = asyncio.Semaphore(self.max_connections)
            async with ClientSession() as session:
                tasks = create_tasks(semaphore, session, resources, action, callback, error_type)
                await asyncio.gather(*tasks)

        asyncio.run(dispatch_action())

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

    def verify(self, resources:  List[Resource], function_name, exception: Callable,
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
        data_context.remove(NEXUS_CONTEXT)
        data_context = data_context[0] if len(data_context) == 1 else data_context
        meta_keys = self.metadata_context.terms.keys()
        metadata = dict()
        data = dict()
        for k, v in payload.items():
            if k in meta_keys:
                metadata[k] = v
            else:
                data[k] = v

        # try to resolve the context
        def resolve(ctx):
            document = dict()
            if isinstance(ctx, list):
                for x in ctx:
                    doc = resolve(x)
                    document.update(doc)
            elif isinstance(ctx, str):
                return self.resolve_context(ctx)
            elif isinstance(ctx, dict):
                document.update(ctx)
            return document

        resolved_ctx = resolve(data_context)
        data["@context"] = resolved_ctx
        resource = _from_jsonld_one(data)
        if isinstance(data_context, str):
            resource.context = data_context
        if len(metadata) > 0:
            self.sync_metadata(resource, metadata)
        return resource
