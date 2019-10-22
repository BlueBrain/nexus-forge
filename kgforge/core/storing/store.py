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
from typing import Dict, Optional, Union

from kgforge.core.commons.attributes import not_supported, repr_
from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData, dispatch
from kgforge.core.resources import Resource, Resources


class Store(ABC):

    # See demo_store.py in kgforge/specializations/stores for an implementation.
    # Specializations should pass tests/specializations/stores/demo_store.feature tests.

    def __init__(self, **kwargs) -> None:
        self.endpoint = kwargs.get("endpoint", None)
        self.bucket = kwargs.get("bucket", None)
        self.token = kwargs.get("token", None)
        # File to resource mapping could be loaded from a Hjson string, a file, or an URL.
        self.file_resource_mapping = kwargs.get("file_resource_mapping", None)

    def __repr__(self) -> str:
        return repr_(self)

    # [C]RUD

    def register(self, data: ManagedData, update: bool) -> None:
        # POLICY Values of type LazyAction should be processed first.
        # POLICY Resource _last_action, _synchronized and _store_metadata should be updated.
        # POLICY Should notify of failures with exception RegistrationError including a message.
        # POLICY Should call actions.run() to update the status and deal with exceptions.
        # POLICY Should print Resource _last_action before returning.
        dispatch(data, self._register_many, self._register_one, update)

    @abstractmethod
    def _register_many(self, resources: Resources, update: bool) -> None:
        # POLICY Follow register() policies.
        pass

    @abstractmethod
    def _register_one(self, resource: Resource, update: bool) -> None:
        # POLICY Follow register() policies.
        pass

    @catch
    def upload(self, path: str) -> ManagedData:
        # TODO Example implementation in DemoStore.
        # TODO The logic is the same as what DemoResolver.resolve() do with terms_resource_mapping.
        # POLICY Should use self.file_resource_mapping to map Store metadata to Model metadata.
        # POLICY Resource _synchronized should be set to True.
        # POLICY Should notify of failures with exception UploadingError including a message.
        p = Path(path)
        return self._upload_many(p) if p.is_dir() else self._upload_one(p)

    def _upload_many(self, dirpath: Path) -> Resources:
        # POLICY Follow upload() policies.
        not_supported()

    def _upload_one(self, filepath: Path) -> Resource:
        # POLICY Follow upload() policies.
        not_supported()

    # C[R]UD

    @catch
    @abstractmethod
    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        # POLICY Resource _synchronized should be set to True and _store_metadata should be set.
        # POLICY Should notify of failures with exception RetrievalError including a message.
        pass

    @catch
    def download(self, data: ManagedData, follow: str, path: str) -> None:
        # TODO Example implementation in DemoStore.
        # POLICY Should notify of failures with exception DownloadingError including a message.
        not_supported()

    # CR[U]D

    def update(self, data: ManagedData) -> None:
        # POLICY Should call Store.register() with update=True.
        # POLICY Follow register() policies.
        self.register(data, update=True)

    def tag(self, data: ManagedData, value: str) -> None:
        # POLICY If the resource is modified by the action, Resource _synchronized should be set
        # POLICY to True and _store_metadata should be set. Otherwise, they should not be changed.
        # POLICY Should notify of failures with exception TaggingError including a message.
        # POLICY Should call actions.run() to update the status and deal with exceptions.
        # POLICY Should print Resource _last_action before returning.
        not_supported()

    # CRU[D]

    def deprecate(self, data: ManagedData) -> None:
        # POLICY Resource _last_action, _synchronized and _store_metadata should be updated.
        # POLICY Should notify of failures with exception DeprecationError including a message.
        # POLICY Should call actions.run() to update the status and deal with exceptions.
        # POLICY Should print Resource _last_action before returning.
        not_supported()

    # Query

    @catch
    @abstractmethod
    def search(self, resolvers: "OntologiesHandler", *filters, **params) -> Resources:
        # Accepted parameters:
        #   - resolving ("exact", "fuzzy")
        #   - lookup ("current", "children")
        # POLICY Resource _synchronized should be set to True and _store_metadata should be set.
        # POLICY Should notify of failures with exception QueryingError including a message.
        pass

    @catch
    def sparql(self, prefixes: Dict[str, str], query: str) -> Resources:
        # TODO Example implementation for a store supporting SPARQL queries.
        # POLICY Follow search() policies.
        not_supported()

    # Versioning

    def freeze(self, data: ManagedData) -> None:
        # POLICY Resource _synchronized and _validated should be set to False.
        # POLICY Should notify of failures with exception FreezingError including a message.
        # POLICY Should call actions.run() with propagate=True to update the status and propagate exceptions.
        # POLICY Should print Resource _last_action before returning.
        not_supported()
