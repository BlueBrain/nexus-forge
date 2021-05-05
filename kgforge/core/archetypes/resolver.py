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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Tuple

from kgforge.core import Resource
from kgforge.core.commons.attributes import repr_class
from kgforge.core.commons.exceptions import ConfigurationError, ResolvingError
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.imports import import_class
from kgforge.core.commons.strategies import ResolvingStrategy

class Resolver(ABC):

    # See demo_resolver.py in kgforge/specializations/resolvers/ for a reference implementation.

    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/resolvers/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Create a generic parameterizable test suite for resolvers. DKE-135.
    # POLICY Implementations should pass tests/specializations/resolvers/test_resolvers.py.

    def __init__(self, source: str, targets: List[Dict[str, str]], result_resource_mapping: str,
                 **source_config) -> None:
        # POLICY Resolver data access should be lazy, unless it takes less than a second.
        # POLICY There could be data caching but it should be aware of changes made in the source.
        self.source: str = source
        self.targets: Dict[str, str] = {x["identifier"]: x["bucket"] for x in targets}
        self.result_mapping: Any = self.mapping.load(result_resource_mapping)
        self.service: Any = self._initialize_service(self.source, self.targets, **source_config)

    def __repr__(self) -> str:
        return repr_class(self)

    @property
    @abstractmethod
    def mapping(self) -> Callable:
        """Mapping class to load result_resource_mapping."""
        pass

    @property
    @abstractmethod
    def mapper(self) -> Callable:
        """Mapper class to map the result data to a Resource with result_resource_mapping."""
        pass

    def resolve(self, text: Union[str, List[str], Resource], target: str, type: str,
                strategy: ResolvingStrategy, resolving_context: Any, property_to_resolve: str, merge_inplace_as: str,
                limit: int, threshold: float) \
            -> Optional[Union[Resource, List[Resource], Dict[str, List[Resource]]]]:

        if isinstance(text, Resource):
            expected = [isinstance(text, Resource), property_to_resolve is not None and hasattr(text, property_to_resolve),
                        isinstance(getattr(text, property_to_resolve), str) or
                        (isinstance(getattr(text, property_to_resolve), list) and all([isinstance(f, str) for f in
                                                                                       getattr(text, property_to_resolve)
                                                                                       ]))]
            if all(expected):
                text_to_resolve = getattr(text, property_to_resolve)
            else:
                raise ResolvingError(
                    "When resolving a Resource, a property_to_resolve of type str or List[str] should be provided")

        elif property_to_resolve is not None or merge_inplace_as is not None:
            not_supported(("property_to_resolve or merge_inplace_as", str))
        else:
            text_to_resolve = text
        # The resolving strategy cannot be abstracted as it should be managed by the service.
        resolved = self._resolve(text_to_resolve, target, type, strategy, resolving_context, limit, threshold)
        if resolved is None or len(resolved) == 0:
            return None
        resolved = resolved[0] if len(resolved) == 1 else resolved
        if isinstance(resolved, tuple):
            # Case Tuple[str,List[Dict]]
            resolved_mapped = self.mapper().map(resolved[1], self.result_mapping, None) if resolved[1] is not None else None
        elif isinstance(text_to_resolve, list):
            # Case List[Tuple[str, List[Dict]]]
            resolved_mapped = {r[0]: self.mapper().map(r[1], self.result_mapping, None) for r in resolved if
                               isinstance(r, tuple)}
        else:
            # Case Dict or List[Dict]
            resolved_mapped = self.mapper().map(resolved, self.result_mapping, None)
        if isinstance(text, Resource) and isinstance(merge_inplace_as, str):
            text.__setattr__(merge_inplace_as, resolved_mapped)
            return text
        else:
            return resolved_mapped

    @abstractmethod
    def _resolve(self, text: Union[str, List[str], Resource], target: str, type: str,
                 strategy: ResolvingStrategy, resolving_context: Any, limit: int, threshold: float) -> Optional[
        List[Any]]:
        # POLICY Should notify of failures with exception ResolvingError including a message.
        pass

    # Utils.

    def _initialize_service(self, source: str, targets: Dict[str, str], **source_config) -> Any:
        # Resolver data could be accessed from a directory, a web service, or a Store.
        # Initialize the access to the resolver data according to the source type.
        # POLICY Should not use 'self'. This is not a function only for the specialization to work.
        origin = source_config.pop("origin")
        if origin == "directory":
            dirpath = Path(source)
            return self._service_from_directory(dirpath, targets, **source_config)
        elif origin == "web_service":
            return self._service_from_web_service(source, targets)
        elif origin == "store":
            store = import_class(source, "stores")
            return self._service_from_store(store, targets, **source_config)
        else:
            raise ConfigurationError(f"unrecognized Resolver origin '{origin}'")

    @staticmethod
    @abstractmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str], **source_config) -> Any:
        pass

    @staticmethod
    def _service_from_web_service(endpoint: str, targets: Dict[str, str]) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, targets: Dict[str, str], **store_config) -> Any:
        not_supported()
