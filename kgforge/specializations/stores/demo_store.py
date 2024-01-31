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
from pathlib import Path
from typing import Dict, List, Optional, Union, Type, Tuple, Any
from uuid import uuid4
from kgforge.core.resource import Resource
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.archetypes.store import Store
from kgforge.core.archetypes.mapper import Mapper
from kgforge.core.archetypes.mapping import Mapping
from kgforge.core.archetypes.model import Model
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import (
    DeprecationError, RegistrationError,
    RetrievalError, TaggingError, UpdatingError
)
from kgforge.core.commons.execution import not_supported
from kgforge.core.conversions.json import as_json, from_json
from kgforge.core.wrappings.dict import wrap_dict, DictWrapper
from kgforge.core.wrappings.paths import create_filters_from_dict, Filter


class DemoStore(Store):
    """An example to show how to implement a Store and to demonstrate how it is used."""

    def __init__(
            self,
            model: Optional[Model] = None,
            endpoint: Optional[str] = None,
            bucket: Optional[str] = None,
            token: Optional[str] = None,
            versioned_id_template: Optional[str] = None,
            file_resource_mapping: Optional[str] = None,
    ) -> None:
        super().__init__(
            model, endpoint, bucket, token, versioned_id_template, file_resource_mapping
        )

    @property
    def context(self) -> Optional[Context]:
        return None

    @property
    def metadata_context(self) -> Optional[Context]:
        return None

    @property
    def mapping(self) -> Type[Mapping]:
        """Mapping class to load file_resource_mapping."""
        return None

    @property
    def mapper(self) -> Type[Mapper]:
        """Mapper class to map file metadata to a Resource with file_resource_mapping."""
        return None

    # [C]RUD.

    def _register_one(self, resource: Resource, schema_id: str) -> None:
        data = as_json(resource, expanded=False, store_metadata=False, model_context=None,
                       metadata_context=None, context_resolver=None)
        try:
            record = self.service.create(data)
        except StoreLibrary.RecordExists as exc:
            raise RegistrationError("resource already exists") from exc

        resource.id = record["data"]["id"]
        resource._store_metadata = wrap_dict(record["metadata"])

    # C[R]UD.

    def retrieve(
            self, id_: str, version: Optional[Union[int, str]],
            cross_bucket: bool = False, **params
    ) -> Optional[Resource]:
        if cross_bucket:
            raise not_supported(("cross_bucket", True))
        try:
            record = self.service.read(id_, version)
        except StoreLibrary.RecordMissing as exc:
            raise RetrievalError("resource not found") from exc

        return _to_resource(record)

    def get_context_prefix_vocab(self) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
        return None, None, None

    # CR[U]D.

    def _update_one(self, resource: Resource, schema_id: str) -> None:
        data = as_json(resource, expanded=False, store_metadata=False, model_context=None,
                       metadata_context=None, context_resolver=None)
        try:
            record = self.service.update(data)
        except StoreLibrary.RecordMissing as exc1:
            raise UpdatingError("resource not found") from exc1
        except StoreLibrary.RecordDeprecated as exc2:
            raise UpdatingError("resource is deprecated") from exc2

        resource._store_metadata = wrap_dict(record["metadata"])

    def _tag_one(self, resource: Resource, value: str) -> None:
        # Chosen case: tagging does not modify the resource.
        rid = resource.id
        version = resource._store_metadata.version
        try:
            self.service.tag(rid, version, value)
        except StoreLibrary.TagExists as exc1:
            raise TaggingError("resource version already tagged") from exc1
        except StoreLibrary.RecordMissing as exc2:
            raise TaggingError("resource not found") from exc2

    # CRU[D].

    def _deprecate_one(self, resource: Resource) -> None:
        rid = resource.id
        try:
            record = self.service.deprecate(rid)
        except StoreLibrary.RecordMissing as exc1:
            raise DeprecationError("resource not found") from exc1
        except StoreLibrary.RecordDeprecated as exc2:
            raise DeprecationError("resource already deprecated") from exc2

        resource._store_metadata = wrap_dict(record["metadata"])

    # Querying.

    def search(
            self, filters: List[Union[Dict, Filter]], resolvers: Optional[List[Resolver]], **params
    ) -> List[Resource]:

        cross_bucket = params.get("cross_bucket", None)
        if cross_bucket is not None:
            raise not_supported(("cross_bucket", True))
        # TODO DKE-145.
        print("<info> DemoStore does not support handling of errors with QueryingError for now.")
        # TODO DKE-145.
        print("<info> DemoStore does not support traversing lists for now.")
        if params:
            # TODO DKE-145.
            print("DemoStore does not support 'resolving' and 'lookup' parameters for now.")
        if filters and isinstance(filters[0], dict):
            filters = create_filters_from_dict(filters[0])
        conditions = [f"x.{'.'.join(x.path)}.{x.operator}({x.value!r})" for x in filters]
        records = self.service.find(conditions)
        return [_to_resource(x) for x in records]

    def _sparql(self, query: str, endpoint: str) -> Optional[Union[List[Resource], Resource]]:
        raise not_supported()

    def _elastic(self, query: str, endpoint: str) -> Optional[Union[List[Resource], Resource]]:
        raise not_supported()

    # Utils.

    def _initialize_service(
            self, endpoint: Optional[str], bucket: Optional[str],
            token: Optional[str], searchendpoints: Optional[Dict] = None, **store_config,
    ):
        return StoreLibrary()

    def _register_many(self, resources: List[Resource], schema_id: str) -> None:
        raise not_supported()

    def _upload_one(self, path: Path, content_type: str) -> Any:
        raise not_supported()

    def _retrieve_filename(self, id: str) -> Tuple[str, str]:
        raise not_supported()

    def _prepare_download_one(self, url: str, store_metadata: Optional[DictWrapper],
                              cross_bucket: bool) -> Tuple[str, str]:
        raise not_supported()

    def _download_one(self, url: str, path: str, store_metadata: Optional[DictWrapper],
                      cross_bucket: bool, content_type: str, bucket: str) -> None:
        raise not_supported()

    def _update_many(self, resources: List[Resource], schema_id: Optional[str]) -> None:
        raise not_supported()

    def _tag_many(self, resources: List[Resource], value: str) -> None:
        raise not_supported()

    def _deprecate_many(self, resources: List[Resource]) -> None:
        raise not_supported()

    def _sparql(self, query: str, endpoint: Optional[str]) -> List[Resource]:
        raise not_supported()

    def _elastic(self, query: str, endpoint: Optional[str]) -> List[Resource]:
        raise not_supported()

    def _freeze_many(self, resources: List[Resource]) -> None:
        raise not_supported()

    def rewrite_uri(self, uri: str, context: Context, **kwargs) -> str:
        raise not_supported()


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
        except KeyError as exc:
            raise self.RecordMissing from exc

        return record

    def update(self, data: Dict) -> Dict:
        rid = data.get("id", None)
        try:
            record = self.records[rid]
        except KeyError as exc:
            raise self.RecordMissing from exc

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
        except KeyError as exc:
            raise self.RecordMissing from exc

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
