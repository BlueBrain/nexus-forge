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
from typing import Dict, List, Optional, Union, Type
from uuid import uuid4

from kgforge.core import Resource
from kgforge.core.archetypes import Resolver, Store, Mapper, Mapping
from kgforge.core.archetypes.store import StoreService
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import (DeprecationError, RegistrationError,
                                             RetrievalError, TaggingError, UpdatingError)
from kgforge.core.commons.execution import not_supported
from kgforge.core.conversions.json import as_json, from_json
from kgforge.core.wrappings.dict import wrap_dict
from kgforge.core.wrappings.paths import create_filters_from_dict
from kgforge.specializations.stores.services.demo_store_service import DemoStoreService


class DemoStore(Store):
    """An example to show how to implement a Store and to demonstrate how it is used."""

    def __init__(self, endpoint: Optional[str] = None, bucket: Optional[str] = None,
                 token: Optional[str] = None, versioned_id_template: Optional[str] = None,
                 file_resource_mapping: Optional[str] = None,
                 model_context: Optional[Context] = None) -> None:
        super().__init__(endpoint, bucket, token, versioned_id_template, file_resource_mapping,
                         model_context)

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
        except DemoStoreService.RecordExists:
            raise RegistrationError("resource already exists")
        else:
            resource.id = record["data"]["id"]
            resource._store_metadata = wrap_dict(record["metadata"])

    # C[R]UD.

    def retrieve(self, id: str, version: Optional[Union[int, str]],
                 cross_bucket: bool, **params) -> Resource:
        if cross_bucket:
            not_supported(("cross_bucket", True))
        try:
            record = self.service.read(id, version)
        except DemoStoreService.RecordMissing:
            raise RetrievalError("resource not found")
        else:
            return _to_resource(record)

    # CR[U]D.

    def _update_one(self, resource: Resource, schema_id: str) -> None:
        data = as_json(resource, expanded=False, store_metadata=False, model_context=None,
                       metadata_context=None, context_resolver=None)
        try:
            record = self.service.update(data)
        except DemoStoreService.RecordMissing:
            raise UpdatingError("resource not found")
        except DemoStoreService.RecordDeprecated:
            raise UpdatingError("resource is deprecated")
        else:
            resource._store_metadata = wrap_dict(record["metadata"])

    def _tag_one(self, resource: Resource, value: str) -> None:
        # Chosen case: tagging does not modify the resource.
        rid = resource.id
        version = resource._store_metadata.version
        try:
            self.service.tag(rid, version, value)
        except DemoStoreService.TagExists:
            raise TaggingError("resource version already tagged")
        except DemoStoreService.RecordMissing:
            raise TaggingError("resource not found")

    # CRU[D].

    def _deprecate_one(self, resource: Resource) -> None:
        rid = resource.id
        try:
            record = self.service.deprecate(rid)
        except DemoStoreService.RecordMissing:
            raise DeprecationError("resource not found")
        except DemoStoreService.RecordDeprecated:
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
        if filters and isinstance(filters[0], dict):
            filters = create_filters_from_dict(filters[0])
        conditions = [f"x.{'.'.join(x.path)}.{x.operator}({x.value!r})" for x in filters]
        records = self.service.find(conditions)
        return [_to_resource(x) for x in records]

    # Utils.

    def _initialize_service(
            self,
            endpoint: Optional[str],
            bucket: Optional[str],
            token: Optional[str],
            searchendpoints: Optional[Dict] = None,
            **store_config,
    ) -> DemoStoreService:
        return DemoStoreService()

def _to_resource(record: Dict) -> Resource:
    # TODO This operation might be abstracted in core when other stores will be implemented.
    resource = from_json(record["data"], None)
    resource._store_metadata = wrap_dict(record["metadata"])
    resource._synchronized = True
    return resource

