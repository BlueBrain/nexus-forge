from collections import namedtuple
from pathlib import Path
from typing import Dict, Optional, Union
from uuid import uuid4

from kgforge.core.commons.actions import run
from kgforge.core.commons.attributes import not_supported
from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData
from kgforge.core.commons.wrappers import DictWrapper
from kgforge.core.resources import Resource, Resources
from kgforge.core.storing.exceptions import (DeprecationError, RegistrationError, RetrievalError,
                                             TaggingError)
from kgforge.core.storing.store import Store


class DemoStore(Store):
    """This is an implementation of a Store to perform tests and help implement specializations."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # TODO Example for 'Files mapping could be loaded from a Hjson, a file, or an URL'.
        # TODO Example for a store using 'bucket' and 'token'.
        self._data = {}
        self._archives = {}
        self._tags = {}

    # [C]RUD

    def _register_many(self, resources: Resources, update: bool) -> None:
        run(self._register, resources, "_synchronized", update)

    def _register_one(self, resource: Resource, update: bool) -> None:
        run(self._register, resource, "_synchronized", update)

    def _register(self, resource: Resource, update: bool) -> None:
        # TODO Example for "Values of type LazyAction should be processed first".
        try:
            rid = resource.id
        except AttributeError:
            rid = str(uuid4())
            resource.id = rid
        finally:
            if rid in self._data.keys():
                if update:
                    record = self._data[rid]
                    self._archives[f"{rid}_{record.version}"] = record
                    new_record = Record(_as_data(resource), record.version + 1, record.deprecated)
                    self._data[rid] = new_record
                    _set_metadata(resource, new_record)
                else:
                    raise RegistrationError(f"resource already exists")
            else:
                record = Record(_as_data(resource), 1, False)
                self._data[rid] = record
                _set_metadata(resource, record)

    def upload(self, path: str) -> ManagedData:
        # FIXME
        # POLICY Should use self.files_mapping to map Store metadata to Model metadata.
        # POLICY Resource _synchronized should be set to True.
        # POLICY Should notify of failures with exception UploadingError including a message.
        # POLICY Should be decorated with exceptions.catch() to deal with exceptions.
        p = Path(path)
        return self._upload_many(p) if p.is_dir() else self._upload_one(p)

    def _upload_many(self, dirpath: Path) -> Resources:
        # FIXME
        # POLICY Follow upload() policies.
        not_supported()

    def _upload_one(self, filepath: Path) -> Resource:
        # FIXME
        # POLICY Follow upload() policies.
        not_supported()

    # C[R]UD

    @catch
    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        try:
            if version:
                if isinstance(version, str):
                    version = self._tags[f"{id}_{version}"]
                record = self._archives[f"{id}_{version}"]
            else:
                record = self._data[id]
        except KeyError:
            raise RetrievalError("resource not found")
        else:
            # FIXME Conversion of nested resources.
            resource = _as_resource(record)
            return resource

    def download(self, data: ManagedData, follow: str, path: str) -> None:
        # FIXME Example.
        not_supported()

    # CR[U]D

    def tag(self, data: ManagedData, value: str) -> None:
        run(self._tag_one, data, None, value)

    def _tag_one(self, resource: Resource, value: str) -> None:
        if resource._synchronized:
            key = f"{resource.id}_{value}"
            if key in self._tags:
                raise TaggingError("resource version already tagged")
            else:
                self._tags[key] = resource._store_metadata.version
        else:
            raise TaggingError("resource not synchronized")

    # CRU[D]

    def deprecate(self, data: ManagedData) -> None:
        run(self._deprecate_one, data, None)

    def _deprecate_one(self, resource: Resource) -> None:
        if resource._synchronized:
            rid = resource.id
            record = self._data[rid]
            if record.deprecated:
                raise DeprecationError("resource already deprecated")
            else:
                self._archives[f"{rid}_{record.version}"] = record
                new_record = Record(record.data, record.version + 1, True)
                self._data[rid] = new_record
                _set_metadata(resource, new_record)
        else:
            raise DeprecationError("resource not synchronized")

    # Query

    @catch
    def search(self, resolver, *filters, **params) -> Resources:
        # FIXME Conversion of nested resources.
        # TODO Example for 'Accepted parameters: resolving ("exact", "fuzzy"), lookup ("current", "children")".
        # TODO Example for 'Should notify of failures with exception QueryingError including a message'.
        records = [x for x in self._data.values()]
        for x in filters:
            path = ".".join(x.path)
            condition = f"r.{path}.{x.operator}({x.value!r})"
            records = [r for r in records
                       if eval(condition, {}, {"x": x, "r": DictWrapper.wrap(r.data)})]
        resources = Resources(_as_resource(y) for y in records)
        return resources

    def sparql(self, prefixes: Dict[str, str], query: str) -> Resources:
        # TODO Example for a store supporting SPARQL queries.
        not_supported()

    # Versioning

    def freeze(self, resource: Resource) -> None:
        # FIXME
        # POLICY Resource _synchronized and _validated should be set to False.
        # POLICY Should notify of failures with exception FreezingError including a message.
        # POLICY Should call actions.run() to update the status and deal with exceptions.
        # POLICY Should print Resource _last_action before returning.
        not_supported()


Record = namedtuple("Record", "data, version, deprecated")


def _as_data(resource: Resource) -> Dict:
    return {k: _as_data(v) if isinstance(v, Resource) else v
            for k, v in resource.__dict__.items() if not k.startswith("_")}


def _as_resource(record: Record) -> Resource:
    resource = Resource(**record.data)
    resource._synchronized = True
    _set_metadata(resource, record)
    return resource


def _set_metadata(resource: Resource, record: Record) -> None:
    metadata = record._asdict()
    del metadata["data"]
    resource._store_metadata = DictWrapper.wrap(metadata)
