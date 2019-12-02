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
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import quote_plus

import nest_asyncio
import nexussdk as nexus
from aiohttp import ClientSession

from kgforge.core import Resource
from kgforge.core.archetypes import Store
from kgforge.core.commons.actions import Action
from kgforge.core.commons.exceptions import (DeprecationError, DownloadingError, RegistrationError,
                                             RetrievalError, TaggingError, UpdatingError,
                                             UploadingError)
from kgforge.core.commons.execution import catch, not_supported, run
from kgforge.core.conversions.jsonld import as_jsonld, find_in_context
from kgforge.core.wrappings.dict import wrap_dict
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping


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


class BlueBrainNexus(Store):

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping)
        try:
            self.organisation, self.project = self.bucket.split('/')
        except ValueError:
            raise ValueError("malformed bucket parameter, expecting 'organization/project' like")
        else:
            # FIXME Should use Nexus namespace. DKE-130.
            self._metadata_fields = ("_storage", "_self", "_constrainedBy", "_project", "_rev",
                                     "_deprecated", "_createdAt", "_createdBy", "_updatedAt",
                                     "_updatedBy", "_incoming", "_outgoing")
            # TODO Migrate to self.service.
            nexus.config.set_environment(self.endpoint)
            nexus.config.set_token(self.token)
            self.max_connections = 50
            self.headers = {
                "Authorization": "Bearer " + self.token,
                "Content-Type": "application/ld+json",
                "Accept": "application/ld+json"
            }
            self.url_requests = '/'.join((self.endpoint,
                                          'resources',
                                          quote_plus(self.organisation),
                                          quote_plus(self.project), '_'))
            # This is to make async working on the jupyter notebook
            nest_asyncio.apply()

    @property
    def mapping(self) -> Optional[Callable]:
        return DictionaryMapping

    @property
    def mapper(self) -> Optional[Callable]:
        return DictionaryMapper

    def register(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._register_one, self._register_many, data, required_synchronized=False,
            execute_actions=True, exception=RegistrationError, monitored_status="_synchronized")

    def _register_many(self, resources: List[Resource]) -> None:
        succeeded, failures = self._batch(resources, action=BatchAction.CREATE)
        action_name = f"{self._register_many.__name__}: {BatchAction.CREATE}"
        if succeeded:
            resources_without_context = list()
            for result in succeeded:
                result.resource.id = result.response["@id"]
                if not hasattr(result.resource, '_context'):
                    resources_without_context.append(result.resource)
            if resources_without_context:
                ids_resources = {r.id: r for r in resources_without_context}
                remote_succeed, remote_fail = self._batch(list(ids_resources.keys()),
                                                          action=BatchAction.FETCH)
                if remote_succeed:
                    for remote in remote_succeed:
                        ids_resources[remote.resource.id]._context = remote.resource._context
                        self._synchronize_resource(ids_resources[remote.resource.id],
                                                   remote.response, action_name, True, True)
                if remote_fail:
                    for remote in remote_fail:
                        try:
                            identifier = remote.resource.id
                        except AttributeError:
                            identifier = remote.resource
                        self._synchronize_resource(ids_resources[identifier], remote.response,
                                                   action_name, True, False)
            else:
                self._synchronize_resources(succeeded, action_name, True, True)
        if failures:
            self._synchronize_resources(results=failures, action_name=action_name, succeeded=False,
                                        synchronized=False)

    def _register_one(self, resource: Resource) -> None:
        data = as_jsonld(resource, True, True)
        try:
            response = nexus.resources.create(org_label=self.organisation,
                                              project_label=self.project, data=data)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, RegistrationError)
        else:
            resource.id = response['@id']
            # If resource had no context, update it with the one provided by the store.
            if not hasattr(resource, '_context'):
                remote = self.retrieve(resource.id, None)
                resource._context = remote._context
            self._sync_metadata(resource, response)

    def _upload_one(self, filepath: Path) -> Dict:
        # TODO: the DictionaryMapping should provide the context since is the one creating
        #  the resource from file_resource_mapping !!
        # resource._context = response["@context"]
        try:
            response = nexus.files.create(self.organisation, self.project,
                                          str(filepath.absolute()))
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, UploadingError)
        else:
            return response

    # C[R]UD.

    @catch
    def retrieve(self, id: str, version: Optional[Union[int, str]]) -> Resource:
        try:
            if isinstance(version, int):
                response = nexus.resources.fetch(org_label=self.organisation,
                                                 project_label=self.project,
                                                 resource_id=id, rev=version)
            else:
                response = nexus.resources.fetch(org_label=self.organisation,
                                                 project_label=self.project,
                                                 resource_id=id, tag=version)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, RetrievalError)
        else:
            resource = self._to_resource(response)
            resource._synchronized = True
            self._sync_metadata(resource, response)
            return resource

    def _download_one(self, url: str, path: Path) -> None:
        try:
            # this is a hack since _self and _id have the same uuid
            file_id = url.split("/")[-1]
            if len(file_id) < 1:
                raise DownloadingError("Invalid file name")
            nexus.files.fetch(org_label=self.organisation, project_label=self.project,
                              file_id=file_id, out_filepath=str(path))
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, DownloadingError)

    # CR[U]D.

    def update(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._update_one, self._update_many, data, id_required=True,
            required_synchronized=False, execute_actions=True, exception=UpdatingError,
            monitored_status="_synchronized")

    def _update_many(self, resources: List[Resource]) -> None:
        succeeded, failures = self._batch(resources, action=BatchAction.UPDATE)
        action_name = f"{self._register_many.__name__}: {BatchAction.UPDATE}"
        if succeeded:
            self._synchronize_resources(succeeded, action_name, True, True)
        if failures:
            self._synchronize_resources(results=failures, action_name=action_name, succeeded=False,
                                        synchronized=False)

    def _update_one(self, resource: Resource) -> None:
        data = as_jsonld(resource, True, True)
        try:
            response = nexus.resources.update(data)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, UpdatingError)
        else:
            self._sync_metadata(resource, response)

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        run(self._tag_one, self._tag_many, data, id_required=True, required_synchronized=True,
            exception=TaggingError, value=value)

    def _tag_many(self, resources: List[Resource], value: str) -> None:
        succeeded, failures = self._batch(resources, action=BatchAction.TAG, tag=value)
        action_name = f"{self._tag_many.__name__}: {BatchAction.TAG}"
        if succeeded:
            self._synchronize_resources(succeeded, action_name, True, True)
        if failures:
            self._synchronize_resources(failures, action_name, False, False)

    def _tag_one(self, resource: Resource, value: str) -> None:
        if resource._last_action.operation == "_tag_one" and resource._last_action.succeeded:
            raise TaggingError("The current version of the resource has being already tagged")
        try:
            payload = as_jsonld(resource, True, True)
            response = nexus.resources.tag(payload, value)
            self._sync_metadata(resource, response)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, TaggingError)

    # CRU[D].

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._deprecate_one, self._deprecate_many, data, id_required=True,
            required_synchronized=True, exception=DeprecationError,
            monitored_status="_synchronized")

    def _deprecate_many(self, resources: List[Resource]) -> None:
        succeeded, failures = self._batch(resources, action=BatchAction.DEPRECATE)
        action_name = f"{self._deprecate_many.__name__}: {BatchAction.DEPRECATE}"
        if succeeded:
            self._synchronize_resources(succeeded, action_name, True, True)
        if failures:
            self._synchronize_resources(failures, action_name, False, False)

    def _deprecate_one(self, resource: Resource) -> None:
        try:
            payload = as_jsonld(resource, True, True)
            response = nexus.resources.deprecate(payload)
            self._sync_metadata(resource, response)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, DeprecationError)

    # Utils.

    def _initialize(self, endpoint: Optional[str], bucket: Optional[str],
                    token: Optional[str]) -> Any:
        # TODO Migrate to self.service. Change return type.
        pass

    # Misc

    @classmethod
    def _to_resource(cls, data: Dict) -> Resource:
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

    def _sync_metadata(self, resource: Resource, result: Dict) -> None:
        metadata = {k: v for k, v in result.items() if k in self._metadata_fields}
        resource._store_metadata = wrap_dict(metadata)

    def _synchronize_resources(self, results: BatchResults, action_name: str, succeeded: bool,
                               synchronized: bool) -> None:
        for result in results:
            self._synchronize_resource(result.resource, result.response, action_name, succeeded,
                                       synchronized)

    def _synchronize_resource(self, resource: Resource, response: dict, action_name: str,
                              succeeded: bool, synchronized: bool) -> None:
        error = None if succeeded else f"{response['@type']}: {response['reason']}"
        action = Action(action_name, succeeded, error)
        resource._last_action = action
        resource._synchronized = synchronized
        if succeeded:
            self._sync_metadata(resource, response)

    def _batch(self, resources: List[Resource],
               action: BatchAction, **kwargs) -> (BatchResults, BatchResults):
        loop = asyncio.get_event_loop()
        failure = list()
        success = list()

        async def dispatch_action():
            futures = []
            semaphore = asyncio.Semaphore(self.max_connections)
            async with ClientSession() as session:
                for resource in resources:
                    if action in [action.UPDATE, action.TAG, action.DEPRECATE]:
                        try:
                            rid = resource.id
                        except AttributeError:
                            response = {"@type": "BadPayload",
                                        "reason": "can't update resources that doesn't have id"
                                        }
                            failure.append(BatchResult(resource, response))
                            continue
                    if action == action.CREATE:
                        payload = as_jsonld(resource, True, True)
                        request = asyncio.ensure_future(
                            queue_post(semaphore=semaphore, session=session,
                                       url=self.url_requests, resource=resource, payload=payload))
                    if action == action.UPDATE:
                        url = "/".join((self.url_requests, quote_plus(rid)))
                        if resource._synchronized:
                            response = {"@type": "Unchanged",
                                        "reason": "Resource unchanged, update didn't happened"
                                        }
                            failure.append(BatchResult(resource, response))
                            continue
                        params = {"rev": resource._store_metadata._rev}
                        payload = as_jsonld(resource, True, True)
                        request = asyncio.ensure_future(
                            queue_put(semaphore=semaphore, session=session,
                                      url=url, resource=resource, payload=payload, params=params))
                    if action == action.TAG:
                        url = "/".join((self.url_requests, quote_plus(rid), "tags"))
                        rev = resource._store_metadata._rev
                        params = {"rev": rev}
                        payload = {"tag": kwargs.get("tag"), "rev": rev}
                        request = asyncio.ensure_future(queue_post(semaphore=semaphore,
                                                                   session=session,
                                                                   url=url, resource=resource,
                                                                   payload=payload, params=params))
                    if action == action.DEPRECATE:
                        url = "/".join((self.url_requests, quote_plus(rid)))
                        params = {"rev": resource._store_metadata._rev}
                        request = asyncio.ensure_future(queue_delete(semaphore=semaphore,
                                                                     session=session,
                                                                     url=url, resource=resource,
                                                                     params=params))
                    futures.append(request)
                await asyncio.gather(*futures)

        async def fetch():
            futures = list()
            semaphore = asyncio.Semaphore(self.max_connections)
            async with ClientSession() as session:
                for resource in resources:
                    try:
                        identifier = resource.id
                    except AttributeError:
                        identifier = resource
                    url = "/".join((self.url_requests, quote_plus(identifier)))
                    request = asyncio.ensure_future(queue_get(semaphore, session, url, resource))
                    futures.append(request)
                await asyncio.gather(*futures)

        async def queue_post(semaphore, session, url, resource, payload, params=None):
            async with semaphore:
                await post(session=session, url=url, resource=resource, payload=payload,
                           params=params)

        async def queue_put(semaphore, session, url, resource, payload, params=None):
            async with semaphore:
                await put(session=session, url=url, resource=resource, payload=payload,
                          params=params)

        async def queue_get(semaphore, session, url, resource):
            async with semaphore:
                await get(session, url, resource)

        async def queue_delete(semaphore, session, url, resource, params):
            async with semaphore:
                await delete(session=session, url=url, resource=resource, params=params)

        async def post(session, url, resource, payload, params):
            async with session.post(
                    url, headers=self.headers, data=json.dumps(payload),
                    params=params) as response:
                content = await response.json()
                if response.status == 201:
                    success.append(BatchResult(resource, content))
                else:
                    failure.append(BatchResult(resource, content))

        async def put(session, url, resource, payload, params):
            async with session.put(
                    url, headers=self.headers, data=json.dumps(payload),
                    params=params) as response:
                content = await response.json()
                if response.status == 200:
                    success.append(BatchResult(resource, content))
                else:
                    failure.append(BatchResult(resource, content))

        async def get(session, url, resource):
            async with session.get(url, headers=self.headers) as response:
                response_content = await response.json()
                if response.status == 200:
                    resource = self._to_resource(response_content)
                    success.append(BatchResult(resource, response_content))
                else:
                    failure.append(BatchResult(resource, response_content))

        async def delete(session, url, resource, params):
            async with session.delete(url, headers=self.headers, params=params) as response:
                response_content = await response.json()
                if response.status == 200:
                    success.append(BatchResult(resource, response_content))
                else:
                    failure.append(BatchResult(resource, response_content))

        action_func = {
            BatchAction.CREATE: dispatch_action,
            BatchAction.UPDATE: dispatch_action,
            BatchAction.FETCH: fetch,
            BatchAction.TAG: dispatch_action,
            BatchAction.DEPRECATE: dispatch_action
        }
        loop.run_until_complete(action_func.get(action, not_supported)())
        return success, failure

    @staticmethod
    def _raise_nexus_http_error(error: nexus.HTTPError, error_type: Callable):
        try:
            reason = error.response.json()["reason"]
        except IndexError:
            reason = error.response.text()
        finally:
            raise error_type(reason)
