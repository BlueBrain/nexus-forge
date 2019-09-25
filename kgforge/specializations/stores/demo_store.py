from collections import namedtuple
from typing import Dict, Optional, Union
from uuid import uuid4

from kgforge.core.commons.actions import run
from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData, do
from kgforge.core.commons.wrappers import DictWrapper
from kgforge.core.resources import Resource, Resources
from kgforge.core.storing.exceptions import (DeprecationError, FreezingError, RegistrationError,
                                             RetrievalError, TaggingError)
from kgforge.core.storing.store import Store


class DemoStore(Store):
    """This is an implementation of a Store to perform tests and help implement specializations."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # TODO Example for 'Files mapping could be loaded from a Hjson string, a file, or an URL'.
        # TODO Example for a store using 'bucket' and 'token'.
        self._data = {}
        self._archives = {}
        self._tags = {}

    # [C]RUD

    def _register_many(self, resources: Resources, update: bool) -> None:
        # TODO Example of an optimization for bulk registration.
        run(self._register, resources, status="_synchronized", update=update)

    def _register_one(self, resource: Resource, update: bool) -> None:
        run(self._register, resource, status="_synchronized", update=update)

    def _register(self, resource: Resource, update: bool) -> None:
        # FIXME Example for "Values of type LazyAction should be processed first".
        try:
            rid = resource.id
        except AttributeError:
            rid = str(uuid4())
            resource.id = rid
        finally:
            if rid in self._data.keys():
                if update:
                    record = self._data[rid]
                    key = _key_archives(rid, record.version)
                    self._archives[key] = record
                    new_record = Record(_as_data(resource), record.version + 1, record.deprecated)
                    self._data[rid] = new_record
                    _set_metadata(resource, new_record)
                else:
                    raise RegistrationError("resource already exists")
            else:
                record = Record(_as_data(resource), 1, False)
                self._data[rid] = record
                _set_metadata(resource, record)

    # C[R]UD

    @catch
    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        try:
            if version:
                if isinstance(version, str):
                    tkey = _key_tags(id, version)
                    version = self._tags[tkey]
                akey = _key_archives(id, version)
                record = self._archives[akey]
            else:
                record = self._data[id]
        except KeyError:
            raise RetrievalError("resource not found")
        else:
            resource = _as_resource(record)
            return resource

    # CR[U]D

    def tag(self, data: ManagedData, value: str) -> None:
        run(self._tag_one, data, value=value)

    def _tag_one(self, resource: Resource, value: str) -> None:
        if resource._synchronized:
            key = _key_tags(resource.id, value)
            if key in self._tags:
                raise TaggingError("resource version already tagged")
            else:
                self._tags[key] = resource._store_metadata.version
        else:
            raise TaggingError("resource not synchronized")

    # CRU[D]

    def deprecate(self, data: ManagedData) -> None:
        run(self._deprecate_one, data)

    def _deprecate_one(self, resource: Resource) -> None:
        if resource._synchronized:
            rid = resource.id
            record = self._data[rid]
            if record.deprecated:
                raise DeprecationError("resource already deprecated")
            else:
                key = _key_archives(rid, record.version)
                self._archives[key] = record
                new_record = Record(record.data, record.version + 1, True)
                self._data[rid] = new_record
                _set_metadata(resource, new_record)
        else:
            raise DeprecationError("resource not synchronized")

    # Query

    @catch
    def search(self, resolvers: "OntologiesHandler", *filters, **params) -> Resources:
        # TODO Example for 'Accepted parameters: resolving ("exact", "fuzzy"), lookup ("current", "children")".
        # TODO Example for 'Should notify of failures with exception QueryingError including a message'.
        records = [x for x in self._data.values()]
        for x in filters:
            path = ".".join(x.path)
            condition = f"r.{path}.{x.operator}({x.value!r})"
            records = [r for r in records
                       if eval(condition, {}, {"x": x, "r": DictWrapper._wrap(r.data)})]
        resources = Resources(_as_resource(y) for y in records)
        return resources

    # Versioning

    def freeze(self, data: ManagedData) -> None:
        run(self._freeze_one, data, propagate=True)

    def _freeze_one(self, resource: Resource) -> None:
        for k, v in resource.__dict__.items():
            do(self._freeze_one, v, error=False)
        if hasattr(resource, "id"):
            rid = resource.id
            try:
                rver = resource._store_metadata.version
            except AttributeError:
                raise FreezingError("resource not yet registered")
            else:
                resource.id = _key_archives(rid, rver)


def _key_archives(id: str, version: int) -> str:
    return f"{id}_version={version}"


def _key_tags(id: str, tag: str) -> str:
    return f"{id}_tag={tag}"


# TODO Cleaner conversion between records in the store and resources.
# TODO Use forge.transforming.as_jsonld(resource, compacted=False, store_metadata=False) for data.
# TODO Use a dictionary for store metadata.
# TODO Do conversions with DictionaryMapper and two DictionaryMapping.

Record = namedtuple("Record", "data, version, deprecated")


def _as_data(resource: Resource) -> Dict:
    return {k: _as_data(v) if isinstance(v, Resource) else v
            for k, v in resource.__dict__.items() if not k.startswith("_")}


def _as_resource(record: Record) -> Resource:
    # FIXME Conversion of nested resources.
    resource = Resource(**record.data)
    resource._synchronized = True
    _set_metadata(resource, record)
    return resource


def _set_metadata(resource: Resource, record: Record) -> None:
    metadata = record._asdict()
    del metadata["data"]
    resource._store_metadata = DictWrapper._wrap(metadata)
