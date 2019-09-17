from pathlib import Path
from typing import Optional, Union

from kgforge.core import Resource, Resources
from kgforge.core.commons.actions import Actions, run
from kgforge.core.commons.attributes import should_be_overridden
from kgforge.core.commons.typing import FilePath, Hjson, ManagedData, URL
from kgforge.core.modeling.handlers.ontologies import OntologyResolver
from kgforge.core.transforming import Mapping
from kgforge.specializations.mappers import DictionaryMapper


class Store:

    def __init__(self, file_mapping: Union[Hjson, FilePath, URL], bucket: str, token: str) -> None:
        # FIXME Should implement the loading from a file and an URL.
        # Files mapping could be loaded from a Hjson, a file, or an URL.
        self.files_mapping = Mapping(file_mapping)
        self.bucket = bucket
        self.token = token

    # [C]RUD

    def register(self, data: ManagedData, update: bool) -> None:
        # FIXME Example.
        # POLICY Values of type LazyAction should be processed first.
        # POLICY Should notify of failures with exceptions extending RegistrationError.
        # FIXME Example of updating Resource._store_metadata.
        # POLICY Resource _last_action, _synchronized and _store_metadata should be updated.
        if isinstance(data, Resources):
            return self._register_many(data, update)
        else:
            run(self._register_one, "_synchronized", data, update=update)
            print(data._last_action)

    def _register_many(self, resources: Resources, update: bool) -> None:
        # Could be optimized by overriding the method in the specialization.
        for x in resources:
            run(self._register_one, "_synchronized", x, update=update)
        print(Actions.from_resources(resources))

    def _register_one(self, resource: Resource, update: bool) -> None:
        should_be_overridden()

    def upload(self, path: str) -> ManagedData:
        # POLICY Should call Store.register() with update=False.
        # FIXME Should catch and deal with UploadingError.
        # POLICY Should notify of failures with exceptions extending UploadingError.
        # FIXME Should set Resource _synchronized to True and should set _store_metadata.
        # POLICY Resource _synchronized should be set to True and _store_metadata should be set.
        p = Path(path)
        metadata = self._upload_many(p) if p.is_dir() else self._upload_one(p)
        data = DictionaryMapper(None).map(metadata, self.files_mapping)
        return data

    def _upload_many(self, dirpath: Path) -> Resources:
        # Could be optimized by overriding the method in the specialization.
        return Resources(self._upload_one(x) for x in dirpath.iterdir())

    def _upload_one(self, filepath: Path) -> Resource:
        should_be_overridden()

    # C[R]UD

    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        # FIXME Should catch and deal with RetrievalError.
        # POLICY Should notify of failures with exceptions extending RetrievalError.
        # POLICY Resource _synchronized should be set to True and _store_metadata should be set.
        should_be_overridden()

    def download(self, data: ManagedData, follow: str, path: str) -> None:
        # FIXME Should catch and deal with DownloadingError.
        # POLICY Should notify of failures with exceptions extending DownloadingError.
        should_be_overridden()

    # CR[U]D

    def update(self, data: ManagedData) -> None:
        # POLICY Should call Store.register() with update=True.
        # POLICY Resource _last_action, _synchronized and _store_metadata should be updated.
        self.register(data, update=True)

    def tag_version(self, data: ManagedData, value: str) -> None:
        should_be_overridden()

    # CRU[D]

    def deprecate(self, data: ManagedData) -> None:
        # POLICY Resource _last_action, _synchronized and _store_metadata should be updated.
        should_be_overridden()

    # Query

    def search(self, resolver: OntologyResolver, *filters, **params) -> Resources:
        # POLICY Resource _synchronized should be set to True and ._store_metadata should be set.
        should_be_overridden()

    def sparql(self, query: str) -> Resources:
        # POLICY Resource _synchronized should be set to True and ._store_metadata should be set.
        should_be_overridden()

    # Versioning

    def freeze_links(self, resource: Resource) -> None:
        # POLICY Resource _synchronized and _validated should be set to False.
        should_be_overridden()


class RegistrationError(Exception):

    pass


class UploadingError(Exception):

    pass


class RetrievalError(Exception):

    pass


class DownloadError(Exception):

    pass
