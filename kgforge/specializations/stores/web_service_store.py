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
from typing import Dict, List, Optional, Union, Type, Callable, Tuple
import copy
import asyncio
import requests
from aiohttp import ClientSession
from requests.exceptions import SSLError


from kgforge.core.resource import Resource
from kgforge.core.commons.context import Context
from kgforge.core.archetypes.model import Model
from kgforge.core.archetypes.mapper import Mapper
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.wrappings.dict import DictWrapper
from kgforge.core.archetypes.dataset_store import DatasetStore
from kgforge.specializations.mappers.dictionaries import DictionaryMapper
from kgforge.core.commons.exceptions import ConfigurationError, DownloadingError
from kgforge.core.commons.execution import not_supported, catch_http_error, error_message


from kgforge.core.wrappings.paths import Filter
from kgforge.specializations.stores.web_service.webservice import WebService


class WebServiceStore(DatasetStore):
    """A high-level class to retrieve and create Datasets from a Web Service."""

    def __init__(
        self,
        model: Model,
        endpoint: str,
        request_params: dict,
        token: Optional[str] = None,
        searchendpoints: Optional[Dict] = None,
        health_endpoint: Optional[str] = None,
        **params,
    ):
        super().__init__(model)
        self.health_endpoint = health_endpoint
        params.update({"request_params": request_params})
        self.service = self._initialize_service(endpoint=endpoint,
                                                token=token,
                                                searchendpoints=searchendpoints,
                                                **params)

    @property
    def mapper(self) -> Optional[Type[Mapper]]:
        return DictionaryMapper

    def download(self, urls: Union[str, List[str]],
                 paths: Union[str, List[str]], overwrite: bool = False) -> None:
        # path: DirPath.
        """Download files """
        if isinstance(urls, list):
            # Check consistancy between urls and paths
            if not isinstance(paths, list):
                raise TypeError("Given multiple urls, paths should also be a list.")
            if len(paths) != len(urls):
                raise ValueError(f"Missmatch between urls ({len(urls)}) and paths ({len(paths)}), \
                                   they should be the same amount.")
            self._download_many(urls, paths)
        else:
            self._download_one(urls, paths)

    def _download_many(self, urls: List[str],
                       paths: List[str]) -> None:
        async def _bulk():
            loop = asyncio.get_event_loop()
            semaphore = asyncio.Semaphore(self.service.max_connection)
            async with ClientSession(headers=self.service.headers_download) as session:
                tasks = (
                    _create_task(x, y, loop, semaphore, session)
                    for x, y in zip(urls, paths)
                )
                return await asyncio.gather(*tasks)

        def _create_task(url, path, loop, semaphore, session):
            return loop.create_task(
                _download(url, path, semaphore, session)
            )

        async def _download(url, path, semaphore, session):
            async with semaphore:
                params_download = copy.deepcopy(self.service.params.get('download', {}))
                async with session.get(url, params=params_download) as response:
                    catch_http_error(
                            response, DownloadingError,
                            error_message_formatter=lambda e:
                            f"Downloading url {url} failed: {error_message(e)}"
                        )
                    with open(path, "wb") as f:
                        data = await response.read()
                        f.write(data)

        return asyncio.run(_bulk())

    def _download_one(self, url: str, path: str) -> None:
        params_download = copy.deepcopy(self.service.params.get('download', {}))
        response = requests.get(
            url=url,
            headers=self.service.headers_download,
            params=params_download,
            verify=False
        )
        catch_http_error(
            response, DownloadingError,
            error_message_formatter=lambda e: f"Downloading failed: "
                                              f"{error_message(e)}"
        )
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=4096):
                f.write(chunk)

    def _prepare_download_one(self, url: str, store_metadata: Optional[DictWrapper],
                              cross_bucket: bool) -> Tuple[str, str]:
        raise not_supported()

    def retrieve(
        self, id: str, version: Optional[Union[int, str]], cross_bucket: bool, **params
    ) -> Resource:
        raise not_supported()

    def _retrieve_filename(self, id: str) -> str:
        raise not_supported()

    def _search(self, resolvers: Optional[List[Resolver]],
                filters: List[Union[Dict, Filter]],
                **params
                ) -> Optional[List[Resource]]:
        # resolvers are not used, just passed because of previous methods shapes
        if not isinstance(filters, dict):
            raise NotImplementedError('Currently only the use of a dictionary as a filter is implemented')
        searchendpoint = params.pop('searchendpoint', None)
        if searchendpoint:
            if self.service.searchendpoints is None:
                raise ConfigurationError("No searchendpoints were given "
                                         "in the initial configuration.")
            try:
                endpoint = self.service.searchendpoints[searchendpoint]['endpoint']
            except KeyError:
                raise ConfigurationError(f"The {searchendpoint} searchpoint was not given "
                                         "in the initial configuration.")
        else:
            endpoint = self.service.endpoint
        # Combine the two dictionaries
        for flr in filters:
            params.update(flr)
        return self.service.resources_from_request(endpoint, self.service.headers,
                                                   self.service.response_location, **params)

    def _sparql(self, query: str) -> Optional[Union[List[Resource], Resource]]:
        raise not_supported()

    def elastic(
            self, query: str, debug: bool, limit: int = None, offset: int = None, **params
    ) -> Optional[Union[List[Resource], Resource]]:
        raise not_supported()

    def rewrite_uri(self, uri: str, context: Context, **kwargs) -> str:
        raise not_supported()

    def health(self) -> Dict:
        if self.health_endpoint:
            try:
                response = requests.get(self.health_endpoint)
            except Exception as error:
                if isinstance(error, SSLError):
                    response = requests.get(self.health_endpoint, verify=False)
                    catch_http_error(
                                response, requests.HTTPError,
                                error_message_formatter=lambda e:
                                f"Health check failed: {error_message(e)}"
                            )
                    return response.json()
                else:
                    raise ConfigurationError(f"Health check failed: {error_message(error)}")
        else:
            raise ConfigurationError("Health information not found with given configuration. "
                                     "Define health in configuration arguments or set _health.")

    def _initialize_service(self, endpoint: str,
                            token: Optional[str],
                            searchendpoints: Optional[Dict],
                            **params
                            ) -> WebService:
        requests_params = params.pop("request_params")
        # split the parameters before initializing the service
        content_type = requests_params.get("content_type", None)
        if not content_type:
            raise ConfigurationError("Content type not specified in request_params: "
                                     f"{requests_params}")
        accept = requests_params.get("accept", None)
        response_location = requests_params.get("response_location", None)
        files_download = requests_params.get("files_download", None)
        return WebService(endpoint, content_type,
                          accept, response_location,
                          files_download, searchendpoints, **params)