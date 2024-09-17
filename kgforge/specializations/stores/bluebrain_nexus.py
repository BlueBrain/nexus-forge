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

import os
import asyncio
import copy
import collections

import json
import mimetypes
import re
from asyncio import Semaphore, Task, AbstractEventLoop

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Type, Callable
from urllib.parse import quote_plus, unquote, urlparse, parse_qs

import requests
from aiohttp import ClientSession, MultipartWriter, hdrs, ClientResponseError
from aiohttp.hdrs import CONTENT_DISPOSITION, CONTENT_TYPE

from kgforge.core.commons.constants import DEFAULT_REQUEST_TIMEOUT
from kgforge.core.commons.dictionaries import update_dict
from kgforge.core.commons.es_query_builder import ESQueryBuilder
from kgforge.core.commons.sparql_query_builder import (
    SPARQLQueryBuilder,
    format_type,
    CategoryDataType,
)
from kgforge.core.resource import Resource
from kgforge.core.archetypes.store import Store
from kgforge.core.archetypes.mapping import Mapping
from kgforge.core.archetypes.mapper import Mapper
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.commons.actions import LazyAction, Action
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import (
    DeprecationError,
    DownloadingError,
    QueryingError,
    RegistrationError,
    RetrievalError,
    TaggingError,
    UpdatingError,
    UploadingError,
    SchemaUpdateError,
)
from kgforge.core.commons.execution import run, not_supported, catch_http_error
from kgforge.core.commons.files import is_valid_url
from kgforge.core.conversions.json import as_json
from kgforge.core.wrappings.dict import DictWrapper
from kgforge.core.wrappings.paths import Filter, create_filters_from_dict
from kgforge.specializations.mappers.dictionaries import DictionaryMapper
from kgforge.specializations.mappings.dictionaries import DictionaryMapping
from kgforge.specializations.stores.nexus.batch_request_handler import (
    BatchRequestHandler,
    BatchResult,
)
from kgforge.specializations.stores.nexus.service import Service, _error_message
import kgforge.specializations.stores.nexus.prepare_methods as prepare_methods
from kgforge.specializations.stores.nexus.http_helpers import files_create


REQUEST_TIMEOUT = DEFAULT_REQUEST_TIMEOUT
JSON_DECODER = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)


def catch_http_error_nexus(
    r: requests.Response,
    e: Type[BaseException],
    error_message_formatter: Callable = _error_message,
    aiohttp_error=False,
):
    return catch_http_error(
        r,
        e,
        error_message_formatter,
        to_catch=requests.HTTPError if not aiohttp_error else ClientResponseError,
    )


class BlueBrainNexus(Store):

    @property
    def context(self) -> Optional[Context]:
        return self.service.context

    @property
    def metadata_context(self) -> Optional[Context]:
        return self.service.metadata_context

    @property
    def mapping(self) -> Type[Mapping]:
        return DictionaryMapping

    @property
    def mapper(self) -> Type[Mapper]:
        return DictionaryMapper

    def register(
        self, data: Union[Resource, List[Resource]], schema_id: str = None
    ) -> None:
        run(
            self._register_one,
            self._register_many,
            data,
            required_synchronized=False,
            execute_actions=True,
            exception=RegistrationError,
            monitored_status="_synchronized",
            schema_id=schema_id,
        )

    def _register_many(self, resources: List[Resource], schema_id: str) -> None:

        fc_name = self._register_many.__name__

        def register_callback(task: Task):
            result = task.result()
            succeeded = not isinstance(result.response, Exception)

            # This if is the one difference with the default callback
            if succeeded:
                result.resource.id = result.response["@id"]
                if not hasattr(result.resource, "context"):
                    context = self.model_context() or self.context
                    result.resource.context = (
                        context.iri
                        if context.is_http_iri()
                        else context.document["@context"]
                    )

            self.service.synchronize_resource(
                result.resource, result.response, fc_name, succeeded, succeeded
            )

        verified = self.service.verify(
            resources,
            function_name=fc_name,
            exception=RegistrationError,
            id_required=False,
            required_synchronized=False,
            execute_actions=True,
        )

        BatchRequestHandler.batch_request_on_resources(
            service=self.service,
            resources=verified,
            callback=register_callback,
            prepare_function=prepare_methods.prepare_create,
            schema_id=schema_id,
        )

    def _register_one(self, resource: Resource, schema_id: str) -> None:
        method, url, resource, exception_, headers, params, payload = (
            prepare_methods.prepare_create(
                service=self.service, resource=resource, schema_id=schema_id
            )
        )
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=True),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        catch_http_error_nexus(response, exception_)

        data = payload

        response_json = response.json()
        resource.id = response_json["@id"]
        # If resource had no context, update it with the one provided by the store.
        if not hasattr(resource, "context"):
            resource.context = data["@context"]

        self.service.sync_metadata(resource, response_json)

    def _upload_many(self, paths: List[Path], content_type: str) -> List[Dict]:
        async def _bulk():
            loop = asyncio.get_event_loop()
            semaphore = Semaphore(self.service.max_connection)
            async with ClientSession(headers=self.service.headers_upload) as session:
                tasks = (_create_task(x, loop, semaphore, session) for x in paths)
                return await asyncio.gather(*tasks)

        def _create_task(path, loop, semaphore, session):
            default = "application/octet-stream"
            mime_type = content_type or mimetypes.guess_type(str(path))[0] or default
            # FIXME Nexus seems to not parse the Content-Disposition 'filename*' field  properly.
            # data = FormData()
            # data.add_field("file", path.open("rb"), content_type=mime_type, filename=path.name)
            # FIXME This hack is to prevent sending Content-Disposition with the 'filename*' field.
            data = MultipartWriter("form-data")
            part = data.append(path.open("rb"))
            part.headers[CONTENT_TYPE] = mime_type
            part.headers[CONTENT_DISPOSITION] = (
                f'form-data; name="file"; filename="{path.name}"'
            )
            return loop.create_task(_upload(data, semaphore, session))

        async def _upload(data, semaphore, session):
            async with semaphore:
                async with session.post(self.service.url_files, data=data) as response:
                    body = await response.json()
                    if response.status < 400:
                        return body

                    msg = " ".join(re.findall("[A-Z][^A-Z]*", body["@type"])).lower()
                    raise UploadingError(msg)

        return asyncio.run(_bulk())

    def _upload_one(self, path: Path, content_type: str) -> Dict:
        file = str(path.absolute())
        mime_type = content_type or mimetypes.guess_type(file, True)[0]
        if mime_type is None:
            mime_type = "application/octet-stream"
        try:
            headers = self.service.headers_upload
            filename = file.split("/")[-1]
            headers[self.service.NEXUS_CONTENT_LENGTH_HEADER] = str(
                os.path.getsize(file)
            )
            file_obj = {"file": (filename, open(file, "rb"), mime_type)}
            response = requests.post(
                self.service.url_files, headers=headers, files=file_obj
            )
            response.raise_for_status()

        except requests.HTTPError as e:
            raise UploadingError(_error_message(e)) from e

        return JSON_DECODER.decode(response.text)

    # C[R]UD.

    @staticmethod
    def _local_url_parse(id_value, version_params) -> Tuple[str, Dict]:
        parsed_id = urlparse(id_value)
        fragment = None
        query_params = {}

        # urlparse is not separating fragment and query params when the latter are put after a fragment
        if parsed_id.fragment is not None and "?" in str(parsed_id.fragment):
            fragment_parts = urlparse(parsed_id.fragment)
            query_params = parse_qs(fragment_parts.query)
            fragment = fragment_parts.path
        elif parsed_id.fragment is not None and parsed_id.fragment != "":
            fragment = parsed_id.fragment
        elif parsed_id.query is not None and parsed_id.query != "":
            query_params = parse_qs(parsed_id.query)

        if version_params is not None:
            query_params.update(version_params)

        formatted_fragment = "#" + fragment if fragment is not None else ""
        id_without_query = f"{parsed_id.scheme}://{parsed_id.netloc}{parsed_id.path}{formatted_fragment}"

        return id_without_query, query_params

    async def _retrieve_id(
        self,
        session,
        id_,
        retrieve_source: bool,
        cross_bucket: bool,
        query_params: Dict,
    ):
        """
        Retrieves assuming the provided identifier really is the id
        """
        url_base = (
            self.service.url_resolver if cross_bucket else self.service.url_resources
        )

        url_resource = Service.add_schema_and_id_to_endpoint(
            url_base, schema_id=None, resource_id=id_
        )
        # 4 cases depending on the value of retrieve_source and cross_bucket:
        # retrieve_source = False and cross_bucket = True: metadata in payload
        # retrieve_source = False and cross_bucket = False: metadata in payload
        # retrieve_source = True and cross_bucket = False: metadata in payload with annotate = True
        # retrieve_source = True and cross_bucket = True:
        #   Uses the resolvers endpoint. No metadata if retrieving_source.
        #   https://github.com/BlueBrain/nexus/issues/4717 To fetch separately.
        #   Solution: first API call used to retrieve metadata
        #             afterwards, second API call to retrieve data

        # TODO temporary
        # url = f"{url_resource}/source" if retrieve_source else url_resource
        #
        # # if cross_bucket, no support for /source and metadata.
        # # So this will fetch the right metadata. The source data will be fetched later
        # if cross_bucket:
        #     url = url_resource

        url = url_resource

        async with session.request(
            method=hdrs.METH_GET, url=url, headers=self.service.headers, params=query_params
        ) as response_not_source_with_metadata:
            # turns the retrieved data into a resource
            not_source_with_metadata = await response_not_source_with_metadata.json()

        catch_http_error_nexus(
            response_not_source_with_metadata, RetrievalError, aiohttp_error=True
        )

        try:
            # TODO temporary
            # if not (retrieve_source and cross_bucket):
            #     return self.service.to_resource(not_source_with_metadata)

            if not retrieve_source:
                return self.service.to_resource(not_source_with_metadata)

        except Exception as e:
            raise RetrievalError(e) from e

        # specific case that requires additional fetching of data with source
        _self = not_source_with_metadata.get("_self", None)

        # Retrieves the appropriate data if retrieve_source = True
        if _self:

            return await self._merge_metadata_with_source_data(
                session, _self, not_source_with_metadata, query_params
            )

        raise RetrievalError("Cannot find metadata in payload")

    async def _merge_metadata_with_source_data(
        self, session, _self, data_not_source_with_metadata, query_params
    ):
        async with session.request(
            method=hdrs.METH_GET,
            url=f"{_self}/source",
            headers=self.service.headers,
            params=query_params,
        ) as response_source:
            # turns the retrieved data into a resource
            data_source = await response_source.json()

        catch_http_error_nexus(response_source, RetrievalError, aiohttp_error=True)

        resource = self.service.to_resource(data_source)
        # uses the metadata of the first call
        self.service.synchronize_resource(
            resource, data_not_source_with_metadata, self.retrieve.__name__, True, True
        )
        return resource

    async def _retrieve_self(
        self, session, self_, retrieve_source: bool, query_params: Dict
    ) -> Resource:
        """
        Retrieves assuming the provided identifier is actually the resource's _self field
        """
        # TODO temporary
        # url = f"{self_}/source" if retrieve_source else self_
        url = self_

        async with session.request(
            method=hdrs.METH_GET,
            url=url,
            headers=self.service.headers,
            params=query_params,
        ) as response_not_source_with_metadata:
            # turns the retrieved data into a resource
            not_source_with_metadata = await response_not_source_with_metadata.json()

        catch_http_error_nexus(
            response_not_source_with_metadata, RetrievalError, aiohttp_error=True
        )

        try:
            if not retrieve_source:
                return self.service.to_resource(not_source_with_metadata)

        except Exception as e:
            raise RetrievalError(e) from e

        return await self._merge_metadata_with_source_data(
            session, self_, not_source_with_metadata, query_params
        )

    def _retrieve_one(
        self, id_: str, version: Optional[Union[int, str]], cross_bucket: bool, **params
    ):
        loop = asyncio.get_event_loop()

        async def do():
            async with ClientSession() as session:
                return await self._retrieve(
                    semaphore=asyncio.Semaphore(1),
                    session=session,
                    id_=id_,
                    version=version,
                    cross_bucket=cross_bucket,
                    **params,
                )

        return loop.run_until_complete(do())

    def _retrieve_many(
        self,
        ids: List[str],
        versions: List[Optional[Union[int, str]]],
        cross_bucket: bool,
        **params,
    ) -> List[Optional[Resource]]:

        def create_tasks(
            semaphore: asyncio.Semaphore,
            session: ClientSession,
            loop: AbstractEventLoop,
            ids_: List[Any],
            service,
            **kwargs,
        ) -> List[asyncio.Task]:

            vs = kwargs["versions"]
            tasks = []

            def retrieve_done_callback(task: Task):
                result = task.result()

                succeeded = not isinstance(result, Action)

                if isinstance(result, Resource):
                    self.service.synchronize_resource(
                        resource=result,
                        response=None,
                        action_name=self,
                        succeeded=succeeded,
                        synchronized=succeeded,
                    )

            async def do_catch(id_, version):
                try:
                    resource = await self._retrieve(
                        semaphore=semaphore,
                        session=session,
                        service=service,
                        id_=id_,
                        version=version,
                        **kwargs,
                    )
                    return resource
                except RetrievalError as e:
                    return Action(self._retrieve_many.__name__, False, e)

            for id_, version in zip(ids_, vs):
                batch_result = do_catch(id_, version)
                prepared_request: asyncio.Task = loop.create_task(batch_result)
                prepared_request.add_done_callback(retrieve_done_callback)
                tasks.append(prepared_request)

            return tasks

        batch_results = BatchRequestHandler.batch_request(
            service=self.service,
            task_creator=create_tasks,
            data=ids,
            versions=versions,
            cross_bucket=cross_bucket,
            **params,
        )
        return batch_results

    def retrieve(
        self,
        id_: Union[str, List[str]],
        version: Union[Optional[Union[int, str]], List[Optional[Union[int, str]]]],
        cross_bucket: bool = False,
        **params,
    ) -> Union[List[Optional[Resource]], Optional[Resource]]:
        """
        Retrieve one or many resources by identifier(s) from the configured store and possibly at a given version.

        :param id_: the identifier(s) of the resource(s) to retrieve
        :param version: the version(s) of the resource(s) to retrieve. In case of list identifier and version values are matched by index
        :param cross_bucket: instructs the configured store to whether search beyond the configured bucket (True) or not (False)
        :param params: a dictionary of parameters. Supported parameters are:
              [retrieve_source] whether to retrieve the resource payload as registered in the last update
              (default: True)
        :return: Union[List[Optional[Resource]], Optional[Resource]]
        """

        ids = [id_] if isinstance(id_, str) else id_

        if len(ids) == 1:

            versions = (
                [version] if isinstance(version, (str, int)) else (version or [None])
            )

            return self._retrieve_one(ids[0], versions[0], cross_bucket, **params)

        versions = [None] * len(ids) if version is None else version

        if len(versions) != len(ids):
            raise Exception("As many versions as ids need to be provided")

        return self._retrieve_many(ids, versions, cross_bucket, **params)

    # TODO service.to_resource probably makes requests of its own and should have a callback in prepare_done
    async def _retrieve(
        self,
        semaphore: asyncio.Semaphore,
        session: ClientSession,
        id_: str,
        version: Optional[Union[int, str]],
        cross_bucket: bool = False,
        **params,
    ) -> Optional[Resource]:
        """
        Retrieve a resource by its identifier from the configured store and possibly at a given version.

        :param id_: the resource identifier to retrieve
        :param version: a version of the resource to retrieve
        :param cross_bucket: instructs the configured store to whether search beyond the configured bucket (True) or not (False)
        :param params: a dictionary of parameters. Supported parameters are:
              [retrieve_source] whether to retrieve the resource payload as registered in the last update
              (default: True)
        :return: Resource
        """

        if version is not None:
            if isinstance(version, int):
                version_params = {"rev": version}
            elif isinstance(version, str):
                version_params = {"tag": version}
            else:
                raise RetrievalError("incorrect 'version'")
        else:
            version_params = None

        id_without_query, query_params = BlueBrainNexus._local_url_parse(
            id_value=id_, version_params=version_params
        )

        retrieve_source = params.get("retrieve_source", True)

        # if retrieve_source:
        #     query_params.update({"annotate": True})

        async with semaphore:
            try:
                return await self._retrieve_id(
                    session=session,
                    id_=id_without_query,
                    retrieve_source=retrieve_source,
                    cross_bucket=cross_bucket,
                    query_params=query_params,
                )
            except RetrievalError as er:

                # without org and proj, vs with
                nexus_path_no_bucket = f"{self.service.endpoint}/resources/"
                nexus_path = (
                    nexus_path_no_bucket if cross_bucket else self.service.url_resources
                )

                if not id_without_query.startswith(nexus_path_no_bucket):
                    raise er

                if not id_without_query.startswith(nexus_path):
                    raise RetrievalError(
                        f"Provided resource identifier {id_} is not inside the current bucket, "
                        "use cross_bucket=True to be able to retrieve it"
                    )

                # Try to use the id as it was given
                return await self._retrieve_self(
                    session=session,
                    self_=id_without_query,
                    retrieve_source=retrieve_source,
                    query_params=query_params,
                )

    def _retrieve_file_metadata(self, id_: str) -> Dict:
        response = requests.get(
            id_, headers=self.service.headers, timeout=REQUEST_TIMEOUT
        )
        catch_http_error_nexus(response, DownloadingError)
        metadata = response.json()
        return metadata

    def _retrieve_filename(self, id_: str) -> Tuple[str, str]:
        metadata = self._retrieve_file_metadata(id_)
        return metadata["_filename"], metadata["_mediaType"]

    def _download_many(
        self,
        urls: List[str],
        paths: List[str],
        store_metadata: Optional[DictWrapper],
        cross_bucket: bool,
        content_type: str,
        buckets: List[str],
    ) -> None:
        async def _bulk():
            loop = asyncio.get_event_loop()
            semaphore = Semaphore(self.service.max_connection)
            headers = (
                self.service.headers_download
                if not content_type
                else update_dict(
                    self.service.headers_download, {"Accept": content_type}
                )
            )
            async with ClientSession(headers=headers) as session:
                tasks = (
                    _create_task(x, y, z, b, loop, semaphore, session)
                    for x, y, z, b in zip(urls, paths, store_metadata, buckets)
                )
                return await asyncio.gather(*tasks)

        def _create_task(url, path, store_metadata, bucket, loop, semaphore, session):
            return loop.create_task(
                _download(url, path, store_metadata, bucket, semaphore, session)
            )

        async def _download(url, path, store_metadata, bucket, semaphore, session):
            async with semaphore:
                params_download = copy.deepcopy(self.service.params.get("download", {}))
                async with session.get(url, params=params_download) as response:
                    catch_http_error_nexus(
                        response,
                        DownloadingError,
                        error_message_formatter=lambda e: f"Downloading url {url} from bucket {bucket} failed: {_error_message(e)}",
                    )
                    with open(path, "wb") as f:
                        data = await response.read()
                        f.write(data)

        return asyncio.run(_bulk())

    def _download_one(
        self,
        url: str,
        path: str,
        store_metadata: Optional[DictWrapper],
        cross_bucket: bool,
        content_type: str,
        bucket: str,
    ) -> None:

        params_download = copy.deepcopy(self.service.params.get("download", {}))
        headers = (
            self.service.headers_download
            if not content_type
            else update_dict(self.service.headers_download, {"Accept": content_type})
        )

        response = requests.get(
            url=url, headers=headers, params=params_download, timeout=REQUEST_TIMEOUT
        )
        catch_http_error_nexus(
            response,
            DownloadingError,
            error_message_formatter=lambda e: f"Downloading from bucket {bucket} failed: "
            f"{_error_message(e)}",
        )

        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=4096):
                f.write(chunk)

    def _prepare_download_one_with_org_project(self, url: str, org: str, project: str):
        file_id = url.split("/")[-1]
        file_id = unquote(file_id)
        if len(file_id) < 1:
            raise DownloadingError(f"Invalid file url: {url}")
        if file_id.startswith("http"):
            url_base = url
        else:
            # this is a hack since _self and _id have the same uuid
            url_base = "/".join(
                (
                    self.service.make_endpoint(
                        endpoint=self.service.endpoint,
                        endpoint_type="files",
                        organisation=org,
                        project=project,
                    ),
                    quote_plus(file_id),
                )
            )
        return url_base, f"{org}/{project}"

    def _prepare_download_one(
        self, url: str, store_metadata: Optional[DictWrapper], cross_bucket: bool
    ) -> Tuple[str, str]:
        if cross_bucket:
            if store_metadata is not None:
                project = store_metadata._project.split("/")[-1]
                org = store_metadata._project.split("/")[-2]
            else:
                raise ValueError(
                    f"Downloading non registered file is not allowed when cross_bucket is set to True"
                )
        else:
            org = self.service.organisation
            project = self.service.project

        return self._prepare_download_one_with_org_project(url, org, project)

    # CR[U]D.

    def update(
        self, data: Union[Resource, List[Resource]], schema_id: str = None
    ) -> None:
        run(
            self._update_one,
            self._update_many,
            data,
            id_required=True,
            required_synchronized=False,
            execute_actions=True,
            exception=UpdatingError,
            monitored_status="_synchronized",
            schema_id=schema_id,
        )

    def _update_many(self, resources: List[Resource], schema_id: str) -> None:
        fc_name = self._update_many.__name__

        verified = self.service.verify(
            resources,
            function_name=fc_name,
            exception=UpdatingError,
            id_required=True,
            required_synchronized=False,
            execute_actions=True,
        )

        BatchRequestHandler.batch_request_on_resources(
            service=self.service,
            resources=verified,
            callback=self.service.default_callback(fc_name),
            prepare_function=prepare_methods.prepare_update,
            schema_id=schema_id,
        )

    def _update_one(self, resource: Resource, schema_id: str) -> None:

        method, url, resource, exception_, headers, params, payload = (
            prepare_methods.prepare_update(
                service=self.service, resource=resource, schema_id=schema_id
            )
        )

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=True),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        catch_http_error_nexus(response, exception_)
        self.service.sync_metadata(resource, response.json())

    def delete_schema(self, resource: Union[Resource, List[Resource]]):
        return self.update_schema(resource, schema_id=Service.UNCONSTRAINED_SCHEMA)

    def _update_schema_one(self, resource: Resource, schema_id: str):
        method, url, resource, exception_, headers, params, payload = (
            prepare_methods.prepare_update_schema(
                service=self.service, resource=resource, schema_id=schema_id
            )
        )
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=True),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        catch_http_error_nexus(response, exception_)
        self.service.sync_metadata(resource, response.json())

    def _update_schema_many(self, resources: List[Resource], schema_id: str):
        fc_name = self._update_schema_many.__name__

        verified = self.service.verify(
            resources,
            function_name=fc_name,
            exception=SchemaUpdateError,
            id_required=True,
            required_synchronized=True,
            execute_actions=False,
        )

        BatchRequestHandler.batch_request_on_resources(
            service=self.service,
            resources=verified,
            prepare_function=prepare_methods.prepare_update_schema,
            callback=self.service.default_callback(fc_name),
            schema_id=schema_id,
        )

    def update_schema(self, data: Union[Resource, List[Resource]], schema_id: str):

        if schema_id is None:
            raise Exception("Missing schema id value")

        run(
            self._update_schema_one,
            self._update_schema_many,
            data,
            id_required=True,
            required_synchronized=True,
            exception=SchemaUpdateError,
            schema_id=schema_id,
        )

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        run(
            self._tag_one,
            self._tag_many,
            data,
            id_required=True,
            required_synchronized=True,
            exception=TaggingError,
            value=value,
        )

    def _tag_many(self, resources: List[Resource], value: str) -> None:
        fc_name = self._tag_many.__name__

        verified = self.service.verify(
            resources,
            function_name=fc_name,
            exception=TaggingError,
            id_required=True,
            required_synchronized=True,
            execute_actions=False,
        )
        BatchRequestHandler.batch_request_on_resources(
            service=self.service,
            resources=verified,
            prepare_function=prepare_methods.prepare_tag,
            callback=self.service.default_callback(fc_name),
            tag=value,
        )

    def _tag_one(self, resource: Resource, value: str) -> None:
        method, url, resource, exception_, headers, params, payload = (
            prepare_methods.prepare_tag(
                service=self.service, resource=resource, tag=value
            )
        )

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=True),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        catch_http_error_nexus(response, exception_)
        self.service.sync_metadata(resource, response.json())

    # CRU[D].

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        run(
            self._deprecate_one,
            self._deprecate_many,
            data,
            id_required=True,
            required_synchronized=True,
            exception=DeprecationError,
            monitored_status="_synchronized",
        )

    def _deprecate_many(self, resources: List[Resource]) -> None:
        fc_name = self._deprecate_many.__name__

        verified = self.service.verify(
            resources,
            function_name=fc_name,
            exception=DeprecationError,
            id_required=True,
            required_synchronized=True,
            execute_actions=False,
        )

        BatchRequestHandler.batch_request_on_resources(
            service=self.service,
            resources=verified,
            prepare_function=prepare_methods.prepare_deprecate,
            callback=self.service.default_callback(fc_name),
        )

    def _deprecate_one(self, resource: Resource) -> None:

        method, url, resource, exception_, headers, params, payload = (
            prepare_methods.prepare_deprecate(service=self.service, resource=resource)
        )

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=True),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        catch_http_error_nexus(response, exception_)
        self.service.sync_metadata(resource, response.json())

        # Querying.

    def search(
        self,
        *filters: Union[Dict, Filter],
        resolvers: Optional[List[Resolver]],
        **params,
    ) -> List[Resource]:

        if "filters" in params:
            raise ValueError(
                "A 'filters' key was provided as params. Filters should be provided as iterable."
            )

        if self.model_context() is None:
            raise ValueError("context model missing")

        debug = params.get("debug", False)
        limit = params.get("limit", 100)
        offset = params.get("offset", None)
        deprecated = params.get("deprecated", False)
        cross_bucket = params.get("cross_bucket", False)
        bucket = params.get("bucket", None)
        search_in_graph = params.get("search_in_graph", True)
        distinct = params.get("distinct", False)
        includes = params.get("includes", None)
        excludes = params.get("excludes", None)
        search_endpoint = params.get(
            "search_endpoint",
            Service.SPARQL_ENDPOINT_TYPE,  # default search endpoint is sparql
        )
        valid_endpoints = [Service.SPARQL_ENDPOINT_TYPE, Service.ELASTIC_ENDPOINT_TYPE]

        if search_endpoint not in valid_endpoints:
            raise ValueError(
                f"The provided search_endpoint value '{search_endpoint}' is not supported. "
                f"Supported search_endpoint values are: {valid_endpoints}"
            )

        if bucket and not cross_bucket:
            raise not_supported(("bucket", True))

        if filters:
            if isinstance(filters, (list, tuple)) and len(filters) > 0:
                if filters[0] is None:
                    raise ValueError("Filters cannot be None")
                elif isinstance(filters[0], dict):
                    filters = create_filters_from_dict(filters[0])
            else:
                filters = list(filters)

        if search_endpoint == Service.SPARQL_ENDPOINT_TYPE:
            if includes or excludes:
                raise ValueError(
                    "Field inclusion and exclusion are not supported when using SPARQL"
                )
            if bucket:
                project_filter = f"Filter (?_project = <{'/'.join([self.endpoint, 'projects', bucket])}>)"
            elif not cross_bucket:
                project_filter = f"Filter (?_project = <{'/'.join([self.endpoint, 'projects', self.organisation, self.project])}>)"
            else:
                project_filter = ""

            query_statements, query_filters = SPARQLQueryBuilder.build(
                schema=None,
                resolvers=resolvers,
                context=self.model_context(),
                filters=filters,
            )
            retrieve_source = params.get("retrieve_source", True)
            store_metadata_statements = []
            if retrieve_source:
                _vars = ["?id"]
                for i, k in enumerate(self.service.store_metadata_keys):
                    _vars.append(f"?{k}")
                    store_metadata_statements.insert(
                        i + 2, f"<{self.metadata_context.terms[k].id}> ?{k}"
                    )
                deprecated_filter = f"Filter (?_deprecated = {format_type[CategoryDataType.BOOLEAN](deprecated)})"
                query_filters.append(deprecated_filter)
            else:
                _vars = ["?id", "?_project", "?_rev"]
                store_metadata_statements.append(
                    f"<{self.service.revision_property}> ?_rev"
                )
                store_metadata_statements.append(
                    f"<{self.service.project_property}> ?_project"
                )
                query_statements.append(
                    f"<{self.service.deprecated_property}> {format_type[CategoryDataType.BOOLEAN](deprecated)}"
                )
            query_statements.extend(store_metadata_statements)
            statements = ";\n ".join(query_statements)
            _filters = "\n".join((".\n ".join(query_filters), project_filter))
            query = SPARQLQueryBuilder.create_select_query(
                _vars, f"?id {statements} . \n {_filters}", distinct, search_in_graph
            )
            # support @id and @type
            resources = self.sparql(
                query,
                debug=debug,
                limit=limit,
                offset=offset,
                view=params.get("view", None),
            )
            results = BatchRequestHandler.batch_request_on_resources(
                service=self.service,
                resources=resources,
                prepare_function=prepare_methods.prepare_fetch,
                callback=None,
                retrieve_source=retrieve_source,
            )
            resources = []
            for result in results:
                resource = result.resource
                if retrieve_source:
                    store_metadata_response = as_json(
                        result.resource,
                        expanded=False,
                        store_metadata=False,
                        model_context=None,
                        metadata_context=None,
                        context_resolver=None,
                    )  # store_metadata is obtained from SPARQL (resource) and
                    # not from server (response) because of retrieve_source==True
                else:
                    store_metadata_response = result.response  # dict
                try:
                    resource = self.service.to_resource(result.response)
                except Exception as e:
                    self.service.synchronize_resource(
                        resource,
                        store_metadata_response,
                        self.search.__name__,
                        False,
                        False,
                    )
                    raise ValueError(e) from e
                finally:
                    self.service.synchronize_resource(
                        resource,
                        store_metadata_response,
                        self.search.__name__,
                        True,
                        True,
                    )
                resources.append(resource)
            return resources
        else:
            if isinstance(self.service.elastic_endpoint["view"], LazyAction):
                self.service.elastic_endpoint["view"] = self.service.elastic_endpoint[
                    "view"
                ].execute()

            elastic_mapping = self.service.elastic_endpoint["view"].get("mapping", None)

            default_str_keyword_field = self.service.elastic_endpoint[
                "default_str_keyword_field"
            ]
            deprecated_property_context_term = self.service.metadata_context.find_term(
                self.service.deprecated_property
            )
            project_property_context_term = self.service.metadata_context.find_term(
                self.service.project_property
            )
            filters.append(
                Filter(
                    operator="__eq__",
                    path=[
                        (
                            deprecated_property_context_term.name
                            if deprecated_property_context_term is not None
                            else "_deprecated"
                        )
                    ],
                    value=deprecated,
                )
            )
            _project = None
            if bucket:
                _project = "/".join([self.endpoint, "projects", bucket])

            elif not cross_bucket:
                _project = "/".join(
                    [self.endpoint, "projects", self.organisation, self.project]
                )

            if _project:
                filters.append(
                    Filter(
                        operator="__eq__",
                        path=[
                            (
                                project_property_context_term.name
                                if project_property_context_term is not None
                                else "_project"
                            )
                        ],
                        value=_project,
                    )
                )

            query = ESQueryBuilder.build(
                elastic_mapping,
                resolvers,
                self.model_context(),
                filters,
                default_str_keyword_field=default_str_keyword_field,
                includes=includes,
                excludes=excludes,
            )

            return self.elastic(
                json.dumps(query),
                debug=debug,
                limit=limit,
                offset=offset,
                view=params.get("view", None),
            )

    @staticmethod  # for testing
    def reformat_contexts(model_context: Context, metadata_context: Optional[Context]):
        ctx = {}

        if metadata_context and metadata_context.document:
            ctx.update(BlueBrainNexus._context_to_dict(metadata_context))

        ctx.update(BlueBrainNexus._context_to_dict(model_context))

        prefixes = model_context.prefixes

        return ctx, prefixes, model_context.vocab

    def get_context_prefix_vocab(
        self,
    ) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
        return BlueBrainNexus.reformat_contexts(
            self.model_context(), self.service.metadata_context
        )

    def _sparql(self, query: str, view: str) -> List[Resource]:

        endpoint = (
            self.service.sparql_endpoint["endpoint"]
            if view is None
            else self.service.make_query_endpoint_self(view, endpoint_type="sparql")
        )

        response = requests.post(
            endpoint,
            data=query,
            headers=self.service.headers_sparql,
            timeout=REQUEST_TIMEOUT,
        )
        catch_http_error_nexus(response, QueryingError)

        data = response.json()

        context = self.model_context() or self.context
        return SPARQLQueryBuilder.build_resource_from_response(query, data, context)

    def _elastic(
        self,
        query: Dict,
        view: Optional[str],
        as_resource: bool,
        build_resource_from: str,
    ) -> Optional[Union[List[Resource], Resource, List[Dict], Dict]]:

        endpoint = (
            self.service.elastic_endpoint["endpoint"]
            if view is None
            else self.service.make_query_endpoint_self(view, endpoint_type="elastic")
        )

        response = requests.post(
            endpoint,
            data=json.dumps(query),
            headers=self.service.headers_elastic,
            timeout=REQUEST_TIMEOUT,
        )
        catch_http_error_nexus(response, QueryingError)

        results = response.json()
        results = results["hits"]["hits"]

        if not as_resource:
            return results

        supported_build_arg = {"source": "_source"}

        if build_resource_from not in supported_build_arg.keys():
            raise Exception(
                f"Building resources is only supported from the following options:"
                f" {supported_build_arg.keys()}"
            )

        key_to_build_from = supported_build_arg[build_resource_from]

        return [
            self.service.to_resource(
                hit[key_to_build_from],
                True,
                **{
                    "id": hit.get("_id", None),
                    "_index": hit.get("_index", None),
                    "_score": hit.get("_score", None),
                },
            )
            for hit in results
        ]

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
            self.organisation, self.project = self.bucket.split("/")
            max_connection = store_config.pop("max_connection", 50)
            if max_connection <= 0:
                raise ValueError(
                    f"max_connection value should be great than 0 but {max_connection} is provided"
                )
            store_context_config = store_config.pop("vocabulary", {})
            nexus_metadata_context = store_context_config.get(
                "metadata",
                {
                    "iri": Service.NEXUS_CONTEXT_FALLBACK,
                    "local_iri": Service.NEXUS_CONTEXT_FALLBACK,
                },
            )
            nexus_context_iri = nexus_metadata_context.get("iri")
            nexus_context_local_iri = nexus_metadata_context.get("local_iri")
            namespace = store_context_config.get(
                "namespace", Service.NEXUS_NAMESPACE_FALLBACK
            )
            project_property = store_context_config.get(
                "project_property", Service.PROJECT_PROPERTY_FALLBACK
            )
            deprecated_property = store_context_config.get(
                "deprecated_property", Service.DEPRECATED_PROPERTY_FALLBACK
            )
            content_type = store_config.pop("Content-Type", "application/ld+json")
            accept = store_config.pop("Accept", "application/ld+json")
            files_upload_config = store_config.pop(
                "files_upload", {"Accept": "application/ld+json"}
            )
            files_download_config = store_config.pop(
                "files_download", {"Accept": "*/*"}
            )
            params = store_config.pop("params", {})
        except Exception as ve:
            raise ValueError(f"Store configuration error: {ve}") from ve

        return Service(
            endpoint=endpoint,
            org=self.organisation,
            prj=self.project,
            token=token,
            model_context=self.model_context(),
            max_connection=max_connection,
            searchendpoints=searchendpoints,
            store_context=nexus_context_iri,
            store_local_context=nexus_context_local_iri,
            namespace=namespace,
            project_property=project_property,
            deprecated_property=deprecated_property,
            content_type=content_type,
            accept=accept,
            files_upload_config=files_upload_config,
            files_download_config=files_download_config,
            **params,
        )

    @staticmethod
    def rewrite_uri_static(
        endpoint: str, bucket: str, uri: str, context: Context, **kwargs
    ) -> str:
        is_file = kwargs.get("is_file", True)
        encoding = kwargs.get("encoding", None)

        # try decoding the url first
        raw_url = unquote(uri)
        if is_file:  # for files
            url_base = "/".join([endpoint, "files", bucket])
        else:  # for resources
            url_base = "/".join([endpoint, "resources", bucket])
        matches = re.match(r"[\w\.:%/-]+/(\w+):(\w+)/[\w\.-/:%]+", raw_url)
        if matches:
            groups = matches.groups()
            old_schema = f"{groups[0]}:{groups[1]}"
            resolved = context.expand(groups[0])
            if raw_url.startswith(url_base):
                extended_schema = resolved + groups[1]
                url = raw_url.replace(old_schema, quote_plus(extended_schema))
                schema_and_id = url.split(url_base + "/")[1]
                id_ = schema_and_id.split(quote_plus(extended_schema) + "/")[-1]
                if not is_valid_url(id_):
                    resolved_id = context.resolve_iri(id_)
                else:
                    resolved_id = id_
                return url.replace(id_, quote_plus(resolved_id))

            extended_schema = "".join([resolved, groups[1]])
            url = raw_url.replace(old_schema, extended_schema)
        else:
            url = raw_url
        if url.startswith(url_base):
            schema_and_id = url.split(url_base)[1]
            if "/_/" in schema_and_id:  # has _ schema
                id_ = schema_and_id.split("/_/")[-1]
            else:
                id_ = schema_and_id.split("/")[-1]
            if not is_valid_url(id_):
                resolved_id = context.resolve_iri(id_)
            else:
                resolved_id = id_
            if resolved_id in schema_and_id:
                return uri  # expanded already given

            return url.replace(id_, quote_plus(resolved_id))
        if not is_file and "/_/" not in url:  # adding _ for empty schema
            uri = "/".join((url_base, "_", quote_plus(url, encoding=encoding)))
        else:
            uri = "/".join((url_base, quote_plus(url, encoding=encoding)))
        return uri

    def rewrite_uri(self, uri: str, context: Context, **kwargs) -> str:
        return BlueBrainNexus.rewrite_uri_static(
            self.endpoint, self.bucket, uri, context, **kwargs
        )

    def _freeze_many(self, resources: List[Resource]) -> None:
        raise not_supported()
