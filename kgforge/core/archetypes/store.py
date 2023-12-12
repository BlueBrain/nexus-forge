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
import json
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List,  Optional, Union, Type

from kgforge.core.archetypes.read_only_store import ReadOnlyStore, DEFAULT_LIMIT, DEFAULT_OFFSET
from kgforge.core.archetypes.model import Model
from kgforge.core.commons import Context
from kgforge.core.resource import Resource
from kgforge.core.archetypes.mapping import Mapping
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.archetypes.mapper import Mapper
from kgforge.core.commons.attributes import repr_class
from kgforge.core.commons.es_query_builder import ESQueryBuilder
from kgforge.core.commons.exceptions import (
    DeprecationError,
    FreezingError,
    RegistrationError,
    TaggingError,
    UpdatingError,
    UploadingError
)
from kgforge.core.commons.execution import run


class Store(ReadOnlyStore):

    # See demo_store.py in kgforge/specializations/stores/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/stores/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Move from BDD to classical testing to have a more parameterizable test suite. DKE-135.
    # POLICY Implementations should pass tests/specializations/stores/demo_store.feature tests.

    def __init__(
            self,
            model: Optional[Model] = None,
            endpoint: Optional[str] = None,
            bucket: Optional[str] = None,
            token: Optional[str] = None,
            versioned_id_template: Optional[str] = None,
            file_resource_mapping: Optional[str] = None,
            searchendpoints: Optional[Dict] = None,
            **store_config,
    ) -> None:
        super().__init__(model)
        self.endpoint: Optional[str] = endpoint
        self.bucket: Optional[str] = bucket
        self.token: Optional[str] = token
        self.versioned_id_template: Optional[str] = versioned_id_template
        self.file_mapping: Optional[Any] = self.mapping.load(file_resource_mapping) \
            if file_resource_mapping else None

        self.service: Any = self._initialize_service(
            self.endpoint, self.bucket, self.token, searchendpoints, **store_config
        )

    def __repr__(self) -> str:
        return repr_class(self)

    @property
    @abstractmethod
    def context(self) -> Optional[Context]:
        ...

    @property
    @abstractmethod
    def metadata_context(self) -> Optional[Context]:
        ...

    @property
    @abstractmethod
    def mapping(self) -> Type[Mapping]:
        """Mapping class to load file_resource_mapping."""
        ...

    @property
    @abstractmethod
    def mapper(self) -> Type[Mapper]:
        """Mapper class to map file metadata to a Resource with file_resource_mapping."""
        ...

    # [C]RUD.

    def register(
            self, data: Union[Resource, List[Resource]], schema_id: str = None
    ) -> None:
        # Replace None by self._register_many to switch to optimized bulk registration.
        run(
            self._register_one,
            None,
            data,
            required_synchronized=False,
            execute_actions=True,
            exception=RegistrationError,
            monitored_status="_synchronized",
            schema_id=schema_id,
        )

    @abstractmethod
    def _register_many(self, resources: List[Resource], schema_id: str) -> None:
        # Bulk registration could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._register_one() and execution._run_one() behaviours.
        ...

    @abstractmethod
    def _register_one(self, resource: Resource, schema_id: str) -> None:
        # POLICY Should notify of failures with exception RegistrationError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        ...

    # This expected that '@catch' is not used here. This is for actions.execute_lazy_actions().
    def upload(
            self, path: str, content_type: str, forge: Optional['KnowledgeGraphForge']
    ) -> Union[Resource, List[Resource]]:
        # path: Union[FilePath, DirPath].
        if self.file_mapping is not None:
            p = Path(path)
            uploaded = self._upload(p, content_type)
            return self.mapper(forge).map(uploaded, self.file_mapping, None)

        raise UploadingError("no file_resource_mapping has been configured")

    def _upload(self, path: Path, content_type: str) -> Union[Any, List[Any]]:
        # path: Union[FilePath, DirPath].
        if path.is_dir():
            filepaths = [
                x for x in path.iterdir() if x.is_file() and not x.name.startswith(".")
            ]
            return self._upload_many(filepaths, content_type)

        return self._upload_one(path, content_type)

    def _upload_many(self, paths: List[Path], content_type: str) -> List[Any]:
        # Bulk uploading could be optimized by overriding this method in the specialization.
        # POLICY Should follow self._upload_one() policies.
        return [self._upload_one(x, content_type) for x in paths]

    @abstractmethod
    def _upload_one(self, path: Path, content_type: str) -> Any:
        # path: FilePath.
        # POLICY Should notify of failures with exception UploadingError including a message.
        ...

    # CR[U]D.

    def update(
            self, data: Union[Resource, List[Resource]], schema_id: Optional[str]
    ) -> None:
        # Replace None by self._update_many to switch to optimized bulk update.
        run(
            self._update_one,
            None,
            data,
            id_required=True,
            required_synchronized=False,
            execute_actions=True,
            exception=UpdatingError,
            monitored_status="_synchronized",
            schema_id=schema_id,
        )

    @abstractmethod
    def _update_many(self, resources: List[Resource], schema_id: Optional[str]) -> None:
        # Bulk update could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._update_one() and execution._run_one() behaviours.
        ...

    @abstractmethod
    def _update_one(self, resource: Resource, schema_id: Optional[str]) -> None:
        # POLICY Should notify of failures with exception UpdatingError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        ...

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        # Replace None by self._tag_many to switch to optimized bulk tagging.
        # POLICY If tagging modify the resource, run() should have status='_synchronized'.
        run(
            self._tag_one,
            None,
            data,
            id_required=True,
            required_synchronized=True,
            exception=TaggingError,
            value=value,
        )

    @abstractmethod
    def _tag_many(self, resources: List[Resource], value: str) -> None:
        # Bulk tagging could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._tag_one() and execution._run_one() behaviours.
        # POLICY If tagging modify the resource, it should be done with status='_synchronized'.
        ...

    @abstractmethod
    def _tag_one(self, resource: Resource, value: str) -> None:
        # POLICY Should notify of failures with exception TaggingError including a message.
        # POLICY If tagging modify the resource, _store_metadata should be updated.
        ...

    # CRU[D].

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        # Replace None by self._deprecate_many to switch to optimized bulk deprecation.
        run(
            self._deprecate_one,
            None,
            data,
            id_required=True,
            required_synchronized=True,
            exception=DeprecationError,
            monitored_status="_synchronized",
        )

    @abstractmethod
    def _deprecate_many(self, resources: List[Resource]) -> None:
        # Bulk deprecation could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._deprecate_one() and execution._run_one() behaviours.
        ...

    @abstractmethod
    def _deprecate_one(self, resource: Resource) -> None:
        # POLICY Should notify of failures with exception DeprecationError including a message.
        # POLICY Resource _store_metadata should be set using wrappers.dict.wrap_dict().
        ...

    # Querying

    def elastic(
            self, query: str, debug: bool, limit: int = DEFAULT_LIMIT, offset: int = DEFAULT_OFFSET
    ) -> List[Resource]:
        query_dict = json.loads(query)

        query_dict = ESQueryBuilder.apply_limit_and_offset_to_query(
            query_dict,
            limit=limit, default_limit=None,
            offset=offset, default_offset=None
        )

        if debug:
            ESQueryBuilder.debug_query(query_dict)

        return self._elastic(json.dumps(query_dict))

    @abstractmethod
    def _elastic(self, query: str) -> Optional[Union[List[Resource], Resource]]:
        # POLICY Should notify of failures with exception QueryingError including a message.
        # POLICY Resource _store_metadata should not be set (default is None).
        # POLICY Resource _synchronized should not be set (default is False).
        ...

    # Versioning.

    def freeze(self, data: Union[Resource, List[Resource]]) -> None:
        # TODO Replace None by self._freeze_many to switch to optimized bulk freezing.
        run(
            self._freeze_one,
            None,
            data,
            id_required=True,
            required_synchronized=True,
            exception=FreezingError,
        )

    @abstractmethod
    def _freeze_many(self, resources: List[Resource]) -> None:
        # Bulk freezing could be optimized by overriding this method in the specialization.
        # POLICY Should reproduce self._freeze_one() and execution._run_one() behaviours.
        ...

    def _freeze_one(self, resource: Resource) -> None:
        # Notify of failures with exception FreezingError including a message.
        # Use self.versioned_id_template.format(x=resource) to freeze IDs.
        for _, v in resource.__dict__.items():
            if isinstance(v, List):
                for x in v:
                    if isinstance(x, Resource):
                        self._freeze_one(x)
            elif isinstance(v, Resource):
                self._freeze_one(v)
        if hasattr(resource, "id"):
            resource.id = self.versioned_id_template.format(x=resource)
