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
import copy
import requests
import asyncio
from aiohttp import ClientSession
from requests.exceptions import SSLError
from typing import Callable, List, Optional, Any

from kgforge.core import Resource
from kgforge.core.archetypes import Database, Store
from kgforge.core.commons.exceptions import ConfigurationError, DownloadingError
from kgforge.core.commons.execution import not_supported, catch
from kgforge.specializations.databases.utils import type_from_filters
from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus, _error_message
from kgforge.specializations.stores.databases import WebService
from kgforge.specializations.resources.datasets import _set


class WebServiceDatabase(Database):
    """A high-level class to retrieve and create Database-related Resources."""
    

    _REQUIRED = ("name", "origin", "source", "model")

    def __init__(self, forge: Optional["KnowledgeGraphForge"],
                 **config) -> None:
        """
        The properties defining the WebServiceDatabase are:

        :param forge: To use forge utilities 
           name: <the name of the database> - REQUIRED
           origin: <'web_service'> - REQUIRED
           source: <a directory path, an URL, or the class name of a Store> - REQUIRED
           bucket: <when 'origin' is 'store', a Store bucket>
           endpoint: <when 'origin' is 'store', a Store endpoint>
           token: <when 'origin' is 'store', a Store token
           model:
             origin: <'directory', 'url', or 'store'>
             source: <a directory path, an URL, or the class name of a Store>
             context: <'directory', 'url', or 'store'>
                bucket: <when 'origin' is 'store', a Store bucket>
                iri: <the IRI of the origin>
        """
        self._check_properties(**config)
        self.name = config.pop('name')
        source = config.pop('source')
        self._health = config.pop('health', None)
        super().__init__(forge, source, **config)

    def _check_properties(self, **info):
        properties = info.keys()
        for r in self._REQUIRED:
            if r not in properties:
                raise ValueError(f'Missing {r} from the properties to define the DatabasSource')

    def search(self, resolvers, *filters, **params):
        """Search within the database.

        :param keep_original: bool 
        """
        keep_original = params.pop('keep_original', True)
        unmapped_resources = self.service.search(resolvers, *filters, **params)
        if isinstance(self.service, BlueBrainNexus) or keep_original:
            return unmapped_resources
        else:
            # Try to find the type of the resources within the filters
            resource_type = type_from_filters(*filters)
            return self.map_resources(unmapped_resources, resource_type=resource_type)
    
    def sparql(self, query: str, debug: bool = False, limit: Optional[int] = None, 
               offset: Optional[int] = None,**params):
        not_supported()
    
    def elastic(**params):
        not_supported()

    @catch
    def attach_file(self, resource, path: str, url: str = None,
                     content_type: str = None,
                     as_part: bool=False, save: bool = False) -> None:
        """Add (different) files as parts or distribution
        
        :param resource: Resource to which attach files
        :param path: DirPath or URL - Location of the file
        :param content_type: the file type
        :param as_part: indicate how to add the file.
        Default adds the file as distribution
        :param save: If path is url, clean up the downloaded files
        """
        if url:
            self._download_one(url, path)
        action = self._forge.attach(path, content_type)
        if as_part:
            distribution = Resource(distribution=action)
            _set(resource, "hasPart", distribution)
        else:
            _set(resource, "distribution", action)

    @catch
    def download(self, urls: str, paths: str, overwrite: bool = False) -> None:
        # path: DirPath.
        """Download files """
        pass

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
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        raise DownloadingError(
                            f"Downloading:{_error_message(e)}"
                        )
                    else:
                        with open(path, "wb") as f:
                            data = await response.read()
                            f.write(data)

        return asyncio.run(_bulk())

    def _download_one(self, url: str, path: str) -> None:
        try:
            params_download = copy.deepcopy(self.service.params.get('download', {}))
            response = requests.get(
                url=url,
                headers=self.service.headers_download,
                params=params_download,
                verify=False
            )
            response.raise_for_status()
        except Exception as e:
            raise DownloadingError(
                f"Downloading from failed :{_error_message(e)}"
            )
        else:
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=4096):
                    f.write(chunk)

    def health(self) -> Callable:
        if self._health:
            try:
                response = requests.get(self._health)
            except SSLError:
                response = requests.get(self._health, verify=False)
            return response.json()
        else:
            raise ConfigurationError('Health information not reachable with given configuration. \
                                      Define health in configuration arguments or set _health.') 

    @staticmethod
    def _service_from_web_service(endpoint: str, **source_config) -> Any:
        return WebService(endpoint, **source_config)

    @staticmethod
    def _service_from_store(store: Callable, **store_config) -> Store:
        not_supported()