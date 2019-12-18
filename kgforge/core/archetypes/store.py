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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from kgforge.core import Resource
from kgforge.core.commons.attributes import repr_class
from kgforge.core.commons.exceptions import (DeprecationError, DownloadingError, FreezingError,
                                             RegistrationError, TaggingError, UpdatingError,
                                             UploadingError)
from kgforge.core.commons.execution import catch, not_supported, run
from kgforge.core.reshaping import collect_values


# NB: Do not 'from kgforge.core.archetypes import Resolver' to avoid cyclic dependency.


class Store(ABC):

    # See demo_store.py in kgforge/specializations/stores/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/stores/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Move from BDD to classical testing to have a more parameterizable test suite. DKE-135.
    # POLICY Implementations should pass tests/specializations/stores/demo_store.feature tests.

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None) -> None:
        # file_resource_mapping: Optional[Union[Hjson, FilePath, URL]].
        self.endpoint: Optional[str] = endpoint
        self.bucket: Optional[str] = bucket
        self.token: Optional[str] = token
        self.versioned_id_template: Optional[str] = versioned_id_template
        loaded = self.mapping.load(file_resource_mapping) if file_resource_mapping else None
        self.file_mapping: Optional[Any] = loaded
        self.service: Any = self._initialize_service(self.endpoint, self.bucket, self.token)

    def __repr__(self) -> str:
        return repr_class(self)

    @property
    def mapping(self) -> Optional[Callable]:
        """Mapping class to load file_resource_mapping."""
        return None

    @property
    def mapper(self) -> Optional[Callable]:
        """Mapper class to map file metadata to a Resource with file_resource_mapping."""
        return None

    # [C]RUD.

    def register(self, data: Union[Resource, List[Resource]]) -> None:
        # Replace None by self._register_many to switch to optimized bulk registration.
        run(self._register_one, None, data, required_synchronized=False, execute_actions=True,
            exception=RegistrationError, monitored_status="_synchronized")

    def _register_many(self, resources: List[Resource]) -> None:
        # Bulk registration could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._register_one() and execution._run_one() behaviours.
        not_supported()

    @abstractmethod
    def _register_one(self, resource: Resource) -> None:
        # POLICY Should notify of failures with exception RegistrationError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # TODO This operation might be abstracted here when other stores will be implemented.
        pass

    # This expected that '@catch' is not used here. This is for actions.execute_lazy_actions().
    def upload(self, path: str) -> Union[Resource, List[Resource]]:
        # path: Union[FilePath, DirPath].
        if self.file_mapping is not None:
            uploaded = self._upload(path)
            return self.mapper().map(uploaded, self.file_mapping)
        else:
            raise UploadingError("no file_resource_mapping has been configured")

    def _upload(self, path: str) -> Union[Any, List[Any]]:
        # path: Union[FilePath, DirPath].
        p = Path(path)
        if p.is_dir():
            filepaths = (x for x in p.iterdir() if x.is_file() and not x.name.startswith("."))
            return self._upload_many(filepaths)
        else:
            return self._upload_one(p)

    def _upload_many(self, filepaths: Iterable[Path]) -> List[Any]:
        # Bulk uploading could be optimized by overriding this method in the specialization.
        # POLICY Should follow self._upload_one() policies.
        return [self._upload_one(x) for x in filepaths]

    def _upload_one(self, filepath: Path) -> Any:
        # POLICY Should notify of failures with exception UploadingError including a message.
        not_supported()

    # C[R]UD.

    @catch
    @abstractmethod
    def retrieve(self, id: str, version: Optional[Union[int, str]]) -> Resource:
        # POLICY Should notify of failures with exception RetrievalError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # POLICY Resource _synchronized should be set to True.
        # TODO These two operations might be abstracted here when other stores will be implemented.
        pass

    @catch
    def download(self, data: Union[Resource, List[Resource]], follow: str, path: str) -> None:
        # path: DirPath.
        urls = collect_values(data, follow, DownloadingError)
        size = len(urls)
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        if size < 1:
            raise DownloadingError("no URLs were found")
        elif size > 1:
            self._download_many(urls, p)
        else:
            self._download_one(urls[0], p)

    def _download_many(self, urls: List[str], path: Path) -> None:
        # path: DirPath.
        # Bulk downloading could be optimized by overriding this method in the specialization.
        # POLICY Should follow self._download_one() policies.
        for x in urls:
            self._download_one(x, path)

    def _download_one(self, url: str, path: Path) -> None:
        # path: DirPath.
        # POLICY Should notify of failures with exception DownloadingError including a message.
        not_supported()

    # CR[U]D.

    def update(self, data: Union[Resource, List[Resource]]) -> None:
        # Replace None by self._update_many to switch to optimized bulk update.
        run(self._update_one, None, data, id_required=True, required_synchronized=False,
            execute_actions=True, exception=UpdatingError, monitored_status="_synchronized")

    def _update_many(self, resources: List[Resource]) -> None:
        # Bulk update could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._update_one() and execution._run_one() behaviours.
        not_supported()

    @abstractmethod
    def _update_one(self, resource: Resource) -> None:
        # POLICY Should notify of failures with exception UpdatingError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # TODO This operation might be abstracted here when other stores will be implemented.
        pass

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        # Replace None by self._tag_many to switch to optimized bulk tagging.
        # POLICY If tagging modify the resource, run() should have status='_synchronized'.
        run(self._tag_one, None, data, id_required=True, required_synchronized=True,
            exception=TaggingError, value=value)

    def _tag_many(self, resources: List[Resource], value: str) -> None:
        # Bulk tagging could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._tag_one() and execution._run_one() behaviours.
        # POLICY If tagging modify the resource, it should be done with status='_synchronized'.
        not_supported()

    def _tag_one(self, resource: Resource, value: str) -> None:
        # POLICY Should notify of failures with exception TaggingError including a message.
        # POLICY If tagging modify the resource, _store_metadata should be updated.
        not_supported()

    # CRU[D].

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        # Replace None by self._deprecate_many to switch to optimized bulk deprecation.
        run(self._deprecate_one, None, data, id_required=True, required_synchronized=True,
            exception=DeprecationError, monitored_status="_synchronized")

    def _deprecate_many(self, resources: List[Resource]) -> None:
        # Bulk deprecation could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._deprecate_one() and execution._run_one() behaviours.
        not_supported()

    def _deprecate_one(self, resource: Resource) -> None:
        # POLICY Should notify of failures with exception DeprecationError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # TODO This operation might be abstracted here when other stores will be implemented.
        not_supported()

    # Querying.

    @catch
    def search(self, resolvers: Optional[List["Resolver"]], *filters, **params) -> List[Resource]:
        # Positional arguments in 'filters' are instances of type Filter from wrappings/paths.py.
        # Keyword arguments in 'params' could be:
        #   - resolving: str, with values in ('exact', 'fuzzy'),
        #   - lookup: str, with values in ('current', 'children').
        # POLICY Should use sparql() when SPARQL is chosen here has the querying language.
        # POLICY Should notify of failures with exception QueryingError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # POLICY Resource _synchronized should be set to True.
        # TODO These two operations might be abstracted here when other stores will be implemented.
        not_supported()

    @catch
    def sparql(self, prefixes: Dict[str, str], query: str) -> List[Resource]:
        # POLICY Should notify of failures with exception QueryingError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        # POLICY Resource _synchronized should be set to True.
        # TODO These two operations might be abstracted here when other stores will be implemented.
        not_supported()

    # Versioning.

    def freeze(self, data: Union[Resource, List[Resource]]) -> None:
        # Replace None by self._freeze_many to switch to optimized bulk freezing.
        run(self._freeze_one, None, data, id_required=True, required_synchronized=True,
            exception=FreezingError)

    def _freeze_many(self, resources: List[Resource]) -> None:
        # Bulk freezing could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._freeze_one() and execution._run_one() behaviours.
        not_supported()

    def _freeze_one(self, resource: Resource) -> None:
        # Notify of failures with exception FreezingError including a message.
        # Use self.versioned_id_template.format(x=resource) to freeze IDs.
        for _, v in resource.__dict__.items():
            if isinstance(v, List):
                for x in v:
                    if isinstance(v, Resource):
                        self._freeze_one(x)
            elif isinstance(v, Resource):
                self._freeze_one(v)
        if hasattr(resource, "id"):
            resource.id = self.versioned_id_template.format(x=resource)

    # Utils.

    @abstractmethod
    def _initialize_service(self, endpoint: Optional[str], bucket: Optional[str],
                            token: Optional[str]) -> Any:
        # POLICY Should initialize the access to the store according to its configuration.
        pass
