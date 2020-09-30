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

from copy import deepcopy
from typing import Dict, List, Optional, Union
from uuid import uuid4

from kgforge.core import Resource
from kgforge.core.archetypes import Resolver, Store
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import (DeprecationError, RegistrationError,
                                             RetrievalError, TaggingError, UpdatingError)
from kgforge.core.commons.execution import not_supported
from kgforge.core.conversions.json import as_json, from_json
from kgforge.core.wrappings.dict import wrap_dict


class DemoStore(Store):
    """An example to show how to implement a Store and to demonstrate how it is used."""

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None,
                 model_context: Optional[Context] = None) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping,
                         model_context)

    # [C]RUD.

    def _register_one(self, resource: Resource, schema_id: str) -> None:
        data = as_json(resource, expanded=False, store_metadata=False, model_context=None,
                       metadata_context=None, context_resolver=None)
        try:
            record = self.service.create(data)
        except StoreLibrary.RecordExists:
            raise RegistrationError("resource already exists")
        else:
            resource.id = record["data"]["id"]
            resource._store_metadata = wrap_dict(record["metadata"])

    # C[R]UD.

    def retrieve(self, id: str, version: Optional[Union[int, str]],
                 cross_bucket: bool) -> Resource:
        if cross_bucket:
            not_supported(("cross_bucket", True))
        try:
            record = self.service.read(id, version)
        except StoreLibrary.RecordMissing:
            raise RetrievalError("resource not found")
        else:
            return _to_resource(record)

    # CR[U]D.

    def _update_one(self, resource: Resource) -> None:
        data = as_json(resource, expanded=False, store_metadata=False, model_context=None,
                       metadata_context=None, context_resolver=None)
        try:
            record = self.service.update(data)
        except StoreLibrary.RecordMissing:
            raise UpdatingError("resource not found")
        except StoreLibrary.RecordDeprecated:
            raise UpdatingError("resource is deprecated")
        else:
            resource._store_metadata = wrap_dict(record["metadata"])

    def _tag_one(self, resource: Resource, value: str) -> None:
        # Chosen case: tagging does not modify the resource.
        rid = resource.id
        version = resource._store_metadata.version
        try:
            self.service.tag(rid, version, value)
        except StoreLibrary.TagExists:
            raise TaggingError("resource version already tagged")
        except StoreLibrary.RecordMissing:
            raise TaggingError("resource not found")

    # CRU[D].

    def _deprecate_one(self, resource: Resource) -> None:
        rid = resource.id
        try:
            record = self.service.deprecate(rid)
        except StoreLibrary.RecordMissing:
            raise DeprecationError("resource not found")
        except StoreLibrary.RecordDeprecated:
            raise DeprecationError("resource already deprecated")
        else:
            resource._store_metadata = wrap_dict(record["metadata"])

    # Querying.

    def search(self, resolvers: Optional[List[Resolver]], *filters, **params) -> List[Resource]:

        cross_bucket = params.get("cross_bucket", None)
        if cross_bucket is not None:
            not_supported(("cross_bucket", True))
        # TODO DKE-145.
        print("<info> DemoStore does not support handling of errors with QueryingError for now.")
        # TODO DKE-145.
        print("<info> DemoStore does not support traversing lists for now.")
        if params:
            # TODO DKE-145.
            print("DemoStore does not support 'resolving' and 'lookup' parameters for now.")
        conditions = [f"x.{'.'.join(x.path)}.{x.operator}({x.value!r})" for x in filters]
        records = self.service.find(conditions)
        return [_to_resource(x) for x in records]

    # Utils.

    def _initialize_service(self, endpoint: Optional[str], bucket: Optional[str],
                            token: Optional[str], searchendpoints:Optional[Dict]):
        return StoreLibrary()


def _to_resource(record: Dict) -> Resource:
    # TODO This operation might be abstracted in core when other stores will be implemented.
    resource = from_json(record["data"], None)
    resource._store_metadata = wrap_dict(record["metadata"])
    resource._synchronized = True
    return resource


class StoreLibrary:
    """Simulate a third-party library handling interactions with the database used by the store."""

    def __init__(self):
        self.records: Dict[str, Dict] = {}
        self.archives: Dict[str, Dict] = {}
        self.tags: Dict[str, int] = {}

    def create(self, data: Dict) -> Dict:
        record = self._record(data, 1, False)
        rid = record["data"]["id"]
        if rid in self.records.keys():
            raise self.RecordExists
        self.records[rid] = record
        return record

    def read(self, rid: str, version: Optional[Union[int, str]]) -> Dict:
        try:
            if version is not None:
                if isinstance(version, str):
                    tkey = self._tag_id(rid, version)
                    version = self.tags[tkey]
                akey = self._archive_id(rid, version)
                record = self.archives[akey]
            else:
                record = self.records[rid]
        except KeyError:
            raise self.RecordMissing
        else:
            return record

    def update(self, data: Dict) -> Dict:
        rid = data.get("id", None)
        try:
            record = self.records[rid]
        except KeyError:
            raise self.RecordMissing
        else:
            metadata = record["metadata"]
            if metadata["deprecated"]:
                raise self.RecordDeprecated
            version = metadata["version"]
            key = self._archive_id(rid, version)
            self.archives[key] = record
            new_record = self._record(data, version + 1, False)
            self.records[rid] = new_record
            return new_record

    def deprecate(self, rid: str) -> Dict:
        try:
            record = self.records[rid]
        except KeyError:
            raise self.RecordMissing
        else:
            metadata = record["metadata"]
            if metadata["deprecated"]:
                raise self.RecordDeprecated
            version = metadata["version"]
            key = self._archive_id(rid, version)
            self.archives[key] = record
            data = record["data"]
            new_record = self._record(data, version + 1, True)
            self.records[rid] = new_record
            return new_record

    def tag(self, rid: str, version: int, value: str) -> None:
        if rid in self.records:
            key = self._tag_id(rid, value)
            if key in self.tags:
                raise self.TagExists
            else:
                self.tags[key] = version
        else:
            raise self.RecordMissing

    def find(self, conditions: List[str]) -> List[Dict]:
        return [r for r in self.records.values()
                if all(eval(c, {}, {"x": wrap_dict(r["data"])}) for c in conditions)]

    def _record(self, data: Dict, version: int, deprecated: bool) -> Dict:
        copy = deepcopy(data)
        if "id" not in copy:
            copy["id"] = self._new_id()
        return {
            "data": copy,
            "metadata": {
                "version": version,
                "deprecated": deprecated,
            },
        }

    @staticmethod
    def _new_id() -> str:
        return str(uuid4())

    @staticmethod
    def _archive_id(rid: str, version: int) -> str:
        return f"{rid}_version={version}"

    @staticmethod
    def _tag_id(rid: str, tag: str) -> str:
        return f"{rid}_tag={tag}"

    class RecordExists(Exception):
        pass

    class RecordMissing(Exception):
        pass

    class RecordDeprecated(Exception):
        pass

    class TagExists(Exception):
        pass
