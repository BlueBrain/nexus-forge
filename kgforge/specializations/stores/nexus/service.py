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
from collections import namedtuple
from enum import Enum
from typing import Dict, List, Callable
from urllib.parse import quote_plus

import nest_asyncio
import nexussdk as nexus
from aiohttp import ClientSession, hdrs

from kgforge.core import Resource
from kgforge.core.conversions.jsonld import find_in_context, as_jsonld


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

# FIXME Should use Nexus namespace. DKE-130.
METADATA_FIELDS = ("_storage", "_self", "_constrainedBy", "_project", "_rev", "_deprecated",
                   "_createdAt", "_createdBy", "_updatedAt", "_updatedBy", "_incoming", "_outgoing")


class Service:

    def __init__(self, endpoint: str, org: str, prj: str, token: str, max_connections: int):

        nexus.config.set_environment(endpoint)
        nexus.config.set_token(token)
        self.project_context = self.get_project_context(org, prj)
        self.max_connections = max_connections
        self.headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/ld+json",
            "Accept": "application/ld+json"
        }
        self.url_resources = '/'.join((endpoint, 'resources', quote_plus(org), quote_plus(prj), '_'))
        self.url_files = '/'.join((endpoint, 'files', quote_plus(org), quote_plus(prj)))
        # This async to work on jupyter notebooks
        nest_asyncio.apply()

    @classmethod
    def get_project_context(cls, organisation: str, project: str) -> Dict:
        project_data = nexus.projects.fetch(organisation, project)
        context = {
            "@base": project_data["base"],
            "@vocab": project_data["vocab"]
        }
        return context

    def batch_request(self, resources: List[Resource], action: BatchAction, callback: Callable,
                      error_type: Callable, **kwargs) -> (BatchResults, BatchResults,):

        def create_tasks(semaphore, session, data, batch_action, f_callback, error):
            futures = []
            for resource in data:
                if batch_action == batch_action.CREATE:
                    payload = as_jsonld(resource, True, False)
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_POST, semaphore, session, self.url_resources, resource,
                              201, error, payload=payload))

                if batch_action == batch_action.UPDATE:
                    url = "/".join((self.url_resources, quote_plus(resource.id)))
                    params = {"rev": resource._store_metadata._rev}
                    payload = as_jsonld(resource, True, False)
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_PUT, semaphore, session, url, resource, 200, error,
                              payload=payload, params=params))

                if batch_action == batch_action.TAG:
                    url = "/".join((self.url_resources, quote_plus(resource.id), "tags"))
                    rev = resource._store_metadata._rev
                    params = {"rev": rev}
                    payload = {"tag": kwargs.get("tag"), "rev": rev}
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_POST, semaphore, session, url, resource, 201, error,
                              payload=payload, params=params))

                if batch_action == batch_action.DEPRECATE:
                    url = "/".join((self.url_resources, quote_plus(resource.id)))
                    params = {"rev": resource._store_metadata._rev}
                    prepared_request = asyncio.create_task(
                        queue(hdrs.METH_DELETE, semaphore, session, url, resource, 200, error,
                              params=params))

                if batch_action == BatchAction.FETCH:
                    try:
                        identifier = resource.id
                    except AttributeError:
                        identifier = resource
                    url = "/".join((self.url_resources, quote_plus(identifier)))
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
                            resource = to_resource(content)
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


def to_resource(data: Dict) -> Resource:
    # FIXME: ideally a rdf-native solution
    def create_resource(dictionary: dict, ctx_base: str) -> Resource:
        rec = Resource()
        if "@id" in dictionary:
            rec.id = f"{ctx_base}{dictionary.pop('@id')}" if ctx_base else dictionary.pop(
                "@id")
        if "@type" in dictionary:
            rec.type = dictionary.pop("@type")
        for k, v in dictionary.items():
            if not re.match(r"^_|@", k):
                # TODO: use nexus namespace to properly identify metadata
                if isinstance(v, dict):
                    setattr(rec, k, create_resource(v, ctx_base))
                elif isinstance(v, list):
                    setattr(rec, k,
                            [create_resource(item, ctx_base) if isinstance(item,
                                                                           dict) else item
                             for item in v])
                else:
                    setattr(rec, k, v)
        return rec

    context = data.pop("@context", None)
    base = find_in_context(context, "@base") if context is not None else None
    resource = create_resource(data, base)
    if context is not None:
        resource._context = context
    return resource
