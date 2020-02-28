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

import mimetypes
from asyncio import Task
from pathlib import Path
from typing import Any, Callable, List, Optional, Union, Dict

import nexussdk as nexus
import re

import requests

from kgforge.core import Resource
from kgforge.core.archetypes import Store
from kgforge.core.commons.actions import collect_lazy_actions, execute_lazy_actions, Action
from kgforge.core.commons.exceptions import (DeprecationError, DownloadingError, RegistrationError,
                                             RetrievalError, TaggingError, UpdatingError,
                                             UploadingError, QueryingError)
from kgforge.core.commons.execution import run
from kgforge.core.conversions.jsonld import as_jsonld
from kgforge.core.wrappings.dict import wrap_dict
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.stores.nexus.service import (Service, to_resource, METADATA_FIELDS,
                                                          BatchAction)


class BlueBrainNexus(Store):

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping)

    @property
    def mapping(self) -> Optional[Callable]:
        return DictionaryMapping

    @property
    def mapper(self) -> Optional[Callable]:
        return DictionaryMapper

    # [C]RUD.

    def register(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._register_one, self._register_many, data, required_synchronized=False,
            execute_actions=True, exception=RegistrationError, monitored_status="_synchronized")

    def _register_many(self, resources: List[Resource]) -> None:

        def register_callback(task: Task):
            result = task.result()
            if isinstance(result.response, Exception):
                _synchronize_resource(
                    result.resource, result.response, self._register_many.__name__, False, False)
            else:
                result.resource.id = result.response["@id"]
                if not hasattr(result.resource, '_context'):
                    result.resource._context = self.service.project_context
                    _synchronize_resource(
                        result.resource, result.response, self._register_many.__name__, True, True)

        validated = _validate(resources, self._register_many.__name__, RegistrationError,
                              id_required=False, required_synchronized=False, execute_actions=True)
        self.service.batch_request(
            validated, BatchAction.CREATE, register_callback, RegistrationError)

    def _register_one(self, resource: Resource) -> None:
        data = as_jsonld(resource, True, True)
        try:
            response = nexus.resources.create(org_label=self.organisation,
                                              project_label=self.project, data=data)
        except nexus.HTTPError as e:
            raise RegistrationError(_error_message(e))
        else:
            resource.id = response['@id']
            # If resource had no context, update it with the one provided by the store.
            if not hasattr(resource, '_context'):
                remote = self.retrieve(resource.id, None)
                resource._context = remote._context
            _sync_metadata(resource, response)

    def _upload_one(self, filepath: Path) -> Dict:
        file = str(filepath.absolute())
        mime_type, _ = mimetypes.guess_type(file, True)
        if mime_type is None:
            mime_type = "application/octet-stream"
        try:
            response = nexus.files.create(self.organisation, self.project, file,
                                          content_type=mime_type)
        except nexus.HTTPError as e:
            raise UploadingError(_error_message(e))
        else:
            return response

    # C[R]UD.

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
            raise RetrievalError(_error_message(e))
        else:
            resource = to_resource(response)
            resource._synchronized = True
            _sync_metadata(resource, response)
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
            raise DownloadingError(_error_message(e))

    # CR[U]D.

    def update(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._update_one, self._update_many, data, id_required=True,
            required_synchronized=False, execute_actions=True, exception=UpdatingError,
            monitored_status="_synchronized")

    def _update_many(self, resources: List[Resource]) -> None:
        update_callback = _default_callback(self._update_many.__name__)
        validated = _validate(resources, self._update_many.__name__, UpdatingError,
                              id_required=True, required_synchronized=False, execute_actions=True)
        self.service.batch_request(validated, BatchAction.UPDATE, update_callback, UpdatingError)

    def _update_one(self, resource: Resource) -> None:
        data = as_jsonld(resource, True, True)
        try:
            response = nexus.resources.update(data)
        except nexus.HTTPError as e:
            raise UpdatingError(_error_message(e))
        else:
            _sync_metadata(resource, response)

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        run(self._tag_one, self._tag_many, data, id_required=True, required_synchronized=True,
            exception=TaggingError, value=value)

    def _tag_many(self, resources: List[Resource], value: str) -> None:
        tag_callback = _default_callback(self._tag_many.__name__)
        validated = _validate(resources, self._tag_many.__name__, TaggingError, id_required=True,
                              required_synchronized=True, execute_actions=False)
        self.service.batch_request(
            validated, BatchAction.TAG, tag_callback, TaggingError, tag=value)

    def _tag_one(self, resource: Resource, value: str) -> None:
        if resource._last_action.operation == "_tag_one" and resource._last_action.succeeded:
            raise TaggingError("The current version of the resource has being already tagged")
        try:
            payload = as_jsonld(resource, True, True)
            response = nexus.resources.tag(payload, value)
            _sync_metadata(resource, response)
        except nexus.HTTPError as e:
            raise TaggingError(_error_message(e))

    # CRU[D].

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        run(self._deprecate_one, self._deprecate_many, data, id_required=True,
            required_synchronized=True, exception=DeprecationError,
            monitored_status="_synchronized")

    def _deprecate_many(self, resources: List[Resource]) -> None:
        deprecate_callback = _default_callback(self._deprecate_many.__name__)
        validated = _validate(resources, self._deprecate_many.__name__, DeprecationError,
                              id_required=True, required_synchronized=True, execute_actions=False)
        self.service.batch_request(
            validated, BatchAction.DEPRECATE, deprecate_callback, DeprecationError)

    def _deprecate_one(self, resource: Resource) -> None:
        try:
            payload = as_jsonld(resource, True, True)
            response = nexus.resources.deprecate(payload)
            _sync_metadata(resource, response)
        except nexus.HTTPError as e:
            raise DeprecationError(_error_message(e))

    # Querying.

    def _sparql(self, query: str) -> List[Resource]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/sparql-query",
        }
        url = f"{self.endpoint}/views/{self.organisation}/{self.project}"
        service = f"{url}/nxv:defaultSparqlIndex/sparql"
        try:
            response = requests.post(service, data=query, headers=headers)
            response.raise_for_status()
        except Exception as e:
            raise QueryingError(e)
        else:
            returned = response.json()
            return [Resource(**{k: v["value"] for k, v in x.items()})
                    for x in returned["results"]["bindings"]]

    # Utils.

    def _initialize_service(self, endpoint: Optional[str], bucket: Optional[str],
                            token: Optional[str]) -> Any:
        try:
            self.organisation, self.project = self.bucket.split('/')
        except ValueError:
            raise ValueError("malformed bucket parameter, expecting 'organization/project' like")
        else:
            return Service(endpoint, self.organisation, self.project, token, 200)


def _default_callback(fun_name: str) -> Callable:
    def callback(task: Task):
        result = task.result()
        if isinstance(result.response, Exception):
            _synchronize_resource(
                result.resource, result.response, fun_name, False, False)
        else:
            _synchronize_resource(
                result.resource, result.response, fun_name, True, True)
    return callback


def _error_message(error: nexus.HTTPError) -> str:
    try:
        content = error.response.json()
        return " ".join(re.findall('[A-Z][^A-Z]*', content["@type"])).lower()
    except AttributeError:
        pass
    try:
        return error.response.text()
    except AttributeError:
        return str(error)


def _validate(resources:  List[Resource], function_name, exception: Callable, id_required: bool,
              required_synchronized: bool, execute_actions: bool) -> List[Resource]:
    valid = list()
    for resource in resources:
        if id_required and not hasattr(resource, "id"):
            error = exception("resource should have an id")
            _synchronize_resource(resource, error, function_name, False, False)
            continue
        if required_synchronized is not None:
            synchronized = resource._synchronized
            if synchronized is not required_synchronized:
                be_or_not_be = "be" if required_synchronized is True else "not be"
                error = exception(f"resource should {be_or_not_be} synchronized")
                _synchronize_resource(resource, error, function_name, False, False)
                continue
        if execute_actions:
            lazy_actions = collect_lazy_actions(resource)
            if lazy_actions is not None:
                try:
                    execute_lazy_actions(resource, lazy_actions)
                except Exception as e:
                    _synchronize_resource(resource, exception(e), function_name, False, False)
                    continue
        valid.append(resource)
    return valid


def _sync_metadata(resource: Resource, result: Dict) -> None:
    metadata = {k: v for k, v in result.items() if k in METADATA_FIELDS}
    resource._store_metadata = wrap_dict(metadata)


def _synchronize_resource(resource: Resource, response: Union[Exception, Dict], action_name: str,
                          succeeded: bool, synchronized: bool) -> None:
    if succeeded:
        action = Action(action_name, succeeded, None)
        _sync_metadata(resource, response)
    else:
        action = Action(action_name, succeeded, response)
    resource._last_action = action
    resource._synchronized = synchronized
