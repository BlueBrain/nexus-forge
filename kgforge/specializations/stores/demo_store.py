from collections import namedtuple
from typing import Dict, Optional, Union

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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data = {}
        self._archives = {}
        self._tags = {}
        self._last_id = -1

    def _new_id(self):
        next_id = self._last_id + 1
        self._last_id = next_id
        return next_id

    # [C]RUD

    def _register_many(self, resources: Resources, update: bool) -> None:
        # TODO Example of an optimization for bulk registration.
        run(self._register, resources, status="_synchronized", update=update)

    def _register_one(self, resource: Resource, update: bool) -> None:
        run(self._register, resource, status="_synchronized", update=update)

    def _register(self, resource: Resource, update: bool) -> None:
        # TODO Example for "Values of type LazyAction should be processed first".
        try:
            rid = resource.id
        except AttributeError:
            rid = self._new_id()
            resource.id = rid
        finally:
            if rid in self._data.keys():
                if update:
                    record = self._data[rid]
                    if record["deprecated"]:
                        raise RegistrationError("resource is deprecated")
                    key = self._key_archives(rid, record["version"])
                    self._archives[key] = record
                    new_record = self._from_resource(resource, record["version"] + 1)
                    self._data[rid] = new_record
                    self._set_metadata(resource, new_record)
                else:
                    raise RegistrationError("resource already exists")
            else:
                record = self._from_resource(resource, 1)
                self._data[rid] = record
                self._set_metadata(resource, record)

    # C[R]UD

    @catch
    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        try:
            if version:
                if isinstance(version, str):
                    tkey = self._key_tags(id, version)
                    version = self._tags[tkey]
                akey = self._key_archives(id, version)
                record = self._archives[akey]
            else:
                record = self._data[id]
        except KeyError:
            raise RetrievalError("resource not found")
        else:
            return self._to_resource(record)

    # CR[U]D

    def tag(self, data: ManagedData, value: str) -> None:
        run(self._tag_one, data, value=value)

    def _tag_one(self, resource: Resource, value: str) -> None:
        if resource._synchronized:
            key = self._key_tags(resource.id, value)
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
            if record["deprecated"]:
                raise DeprecationError("resource already deprecated")
            else:
                key = self._key_archives(rid, record["version"])
                self._archives[key] = record
                new_record = self._from_resource(resource, record["version"] + 1, True)
                self._data[rid] = new_record
                self._set_metadata(resource, new_record)
        else:
            raise DeprecationError("resource not synchronized")

    # Query

    @catch
    def search(self, resolvers: "OntologiesHandler", *filters, **params) -> Resources:
        # TODO Example for 'Accepted parameters: resolving ("exact", "fuzzy"), lookup ("current", "children")".
        records = [x for x in self._data.values()]
        for x in filters:
            path = ".".join(x.path)
            condition = f"r.{path}.{x.operator}({x.value!r})"


            records = [r for r in records
                       if eval(condition, {}, {"x": x, "r": DictWrapper._wrap(r["data"])})]
        resources = Resources(self._to_resource(y) for y in records)
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
                resource.id = self._key_archives(rid, rver)

    # Internals

    @staticmethod
    def _key_archives(id: str, version: int) -> str:
        return f"{id}_version={version}"

    @staticmethod
    def _key_tags(id: str, tag: str) -> str:
        return f"{id}_tag={tag}"

    @staticmethod
    def _from_resource(resource: Resource, version: int, deprecated: bool = False) -> Dict:
        # TODO Use forge.transforming.as_jsonld(resource, compacted=False, store_metadata=False) for data.
        def as_data(resource: Resource) -> Dict:
            return {k: as_data(v) if isinstance(v, Resource) else v
                    for k, v in resource.__dict__.items() if not k in resource._RESERVED}
        return {
            "data": as_data(resource),
            "version": version,
            "deprecated": deprecated,
        }

    def _to_resource(self, record: Dict) -> Resource:
        def as_resource(data: Dict) -> Resource:
            properties = {k: as_resource(v) if isinstance(v, Dict) else v for k, v in data.items()}
            return Resource(**properties)
        resource = as_resource(record["data"])
        self._set_metadata(resource, record)
        return resource

    @staticmethod
    def _set_metadata(resource: Resource, record: Dict) -> None:
        metadata = {k: v for k, v in record.items() if k != "data"}
        resource._synchronized = True
        resource._store_metadata = DictWrapper._wrap(metadata)
