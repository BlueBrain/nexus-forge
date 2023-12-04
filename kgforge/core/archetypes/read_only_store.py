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
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from kgforge.core.resource import Resource
from kgforge.core.archetypes.model import Model
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.commons.attributes import repr_class
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import (
    DownloadingError,
)
from kgforge.core.commons.sparql_query_builder import SPARQLQueryBuilder
from kgforge.core.reshaping import collect_values
from kgforge.core.wrappings import Filter
from kgforge.core.wrappings.dict import DictWrapper

DEFAULT_LIMIT = 100
DEFAULT_OFFSET = 0


class ReadOnlyStore(ABC):

    # See demo_store.py in kgforge/specializations/stores/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/stores/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Move from BDD to classical testing to have a more parameterizable test suite. DKE-135.
    # POLICY Implementations should pass tests/specializations/stores/demo_store.feature tests.

    def __init__(
            self,
            model: Optional[Model] = None,
    ) -> None:
        self.model: Optional[Model] = model

    def __repr__(self) -> str:
        return repr_class(self)

    def get_context_prefix_vocab(self) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
        return (
            Context.context_to_dict(self.model_context()),
            self.model_context().prefixes,
            self.model_context().vocab
        )

    # C[R]UD.

    @abstractmethod
    def retrieve(
            self, id_: str, version: Optional[Union[int, str]], cross_bucket: bool = False, **params
    ) -> Optional[Resource]:
        # POLICY Should notify of failures with exception RetrievalError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # POLICY Resource _synchronized should be set to True.
        # TODO These two operations might be abstracted here when other stores will be implemented.
        ...

    @abstractmethod
    def _retrieve_filename(self, id: str) -> Tuple[str, str]:
        # TODO This operation might be adapted if other file metadata are needed.
        ...

    @abstractmethod
    def _prepare_download_one(
            self,
            url: str,
            store_metadata: Optional[DictWrapper],
            cross_bucket: bool
    ) -> Tuple[str, str]:
        # Prepare download url and download bucket
        ...

    def download(
            self,
            data: Union[Resource, List[Resource]],
            follow: str,
            path: str,
            overwrite: bool,
            cross_bucket: bool,
            content_type: str = None
    ) -> None:
        # path: DirPath.
        urls = []
        store_metadata = []
        to_download = [data] if isinstance(data, Resource) else data
        for d in to_download:
            collected_values = collect_values(d, follow, DownloadingError)
            urls.extend(collected_values)
            store_metadata.extend(
                [d._store_metadata for _ in range(len(collected_values))]
            )
        if len(urls) == 0:
            raise DownloadingError(
                f"path to follow '{follow}' was not found in any provided resource."
            )
        dirpath = Path(path)
        dirpath.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d%H%M%S")
        filepaths = []
        buckets = []
        download_urls = []
        download_store_metadata = []
        for i, x in enumerate(urls):
            x_download_url, x_bucket = self._prepare_download_one(x, store_metadata[i],
                                                                  cross_bucket)
            filename, store_content_type = self._retrieve_filename(x_download_url)
            if not content_type or (content_type and store_content_type == content_type):
                filepath = dirpath / filename
                if not overwrite and filepath.exists():
                    filepaths.append(f"{filepath}.{timestamp}")
                else:
                    filepaths.append(str(filepath))
                download_urls.append(x_download_url)
                buckets.append(x_bucket)
                download_store_metadata.append(store_metadata[i])
        if len(download_urls) > 1:
            self._download_many(download_urls, filepaths, download_store_metadata, cross_bucket,
                                content_type, buckets)
        elif len(download_urls) == 1:
            self._download_one(download_urls[0], filepaths[0], download_store_metadata[0],
                               cross_bucket, content_type, buckets[0])
        else:
            raise DownloadingError(
                f"No resource with content_type {content_type} was found when following the resource path '{follow}'."
            )

    def _download_many(
            self,
            urls: List[str],
            paths: List[str],
            store_metadata: Optional[List[DictWrapper]],
            cross_bucket: bool,
            content_type: str,
            buckets: List[str]
    ) -> None:
        # paths: List[FilePath].
        # Bulk downloading could be optimized by overriding this method in the specialization.
        # POLICY Should follow self._download_one() policies.
        for url, path, store_m, bucket in zip(urls, paths, store_metadata, buckets):
            self._download_one(url, path, store_m, cross_bucket, content_type, bucket)

    @abstractmethod
    def _download_one(
            self,
            url: str,
            path: str,
            store_metadata: Optional[DictWrapper],
            cross_bucket: bool,
            content_type: str,
            bucket: str
    ) -> None:
        # path: FilePath.
        # POLICY Should notify of failures with exception DownloadingError including a message.
        ...

    # Querying.

    @abstractmethod
    def search(
            self, resolvers: Optional[List[Resolver]], filters: List[Union[Dict, Filter]], **params
    ) -> List[Resource]:

        # Positional arguments in 'filters' are instances of type Filter from wrappings/paths.py
        # A dictionary can be provided for filters:
        #  - {'key1': 'val', 'key2': {'key3': 'val'}} will be translated to
        #  - [Filter(operator='__eq__', path=['key1'], value='val'), Filter(operator='__eq__', path=['key2', 'key3'], value='val')]
        # Keyword arguments in 'params' could be:
        #   - debug: bool,
        #   - limit: int,
        #   - offset: int,
        #   - deprecated: bool,
        #   - resolving: str, with values in ('exact', 'fuzzy'),
        #   - lookup: str, with values in ('current', 'children').
        # POLICY Should use sparql() when 'sparql' is chosen as value  for the param 'search_endpoint'.
        # POLICY Should use elastic() when 'elastic' is chosen as value  for the param 'search_endpoint'.
        # POLICY Given parameters for limit and offset override the input query.
        # POLICY Should notify of failures with exception QueryingError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # POLICY Resource _synchronized should be set to True.
        # TODO These two operations might be abstracted here when other stores will be implemented.
        ...

    def sparql(
            self, query: str,
            debug: bool,
            limit: int = DEFAULT_LIMIT,
            offset: int = DEFAULT_OFFSET,
            **params
    ) -> List[Resource]:
        rewrite = params.get("rewrite", True)

        if self.model_context() is not None and rewrite:

            context_as_dict, prefixes, vocab = self.get_context_prefix_vocab()

            qr = SPARQLQueryBuilder.rewrite_sparql(
                query,
                context_as_dict=context_as_dict,
                prefixes=prefixes,
                vocab=vocab
            )
        else:
            qr = query

        qr = SPARQLQueryBuilder.apply_limit_and_offset_to_query(
            qr,
            limit=limit,
            offset=offset,
            default_limit=DEFAULT_LIMIT,
            default_offset=DEFAULT_OFFSET
        )

        if debug:
            SPARQLQueryBuilder.debug_query(qr)

        return self._sparql(qr)

    @abstractmethod
    def _sparql(self, query: str) -> Optional[Union[List[Resource], Resource]]:
        # POLICY Should notify of failures with exception QueryingError including a message.
        # POLICY Resource _store_metadata should not be set (default is None).
        # POLICY Resource _synchronized should not be set (default is False).
        ...

    @abstractmethod
    def elastic(
            self, query: str, debug: bool, limit: int = None,
            offset: int = None, **params
    ) -> Optional[Union[List[Resource], Resource]]:
        ...

    # Versioning.

    @abstractmethod
    def _initialize_service(
            self,
            endpoint: Optional[str],
            bucket: Optional[str],
            token: Optional[str],
            searchendpoints: Optional[Dict] = None,
            **store_config,
    ) -> Any:
        # POLICY Should initialize the access to the store according to its configuration.
        ...

    @abstractmethod
    def rewrite_uri(self, uri: str, context: Context, **kwargs) -> str:
        """Rewrite a given uri using the store Context
        :param uri: a URI to rewrite.
        :param context: a Store Context object
        :return: str
        """
        ...

    def model_context(self):
        return self.model.context() if self.model else None
