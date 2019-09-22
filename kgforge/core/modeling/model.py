from abc import ABC, abstractmethod
from typing import Dict, List, Union

from kgforge.core.commons.attributes import not_supported
from kgforge.core.commons.typing import DirPath, Hjson, ManagedData, URL, dispatch
from kgforge.core.resources import Resource, Resources
from kgforge.core.storing.store import Store


class Model(ABC):

    # See demo_model.py in specializations/models for implementation.

    def __init__(self, source: Union[DirPath, URL, Store]) -> None:
        # Schemas could be loaded from a directory, an URL, or the store.
        # The strategy to get the relevant data should be lazy and could depend on the objective.
        # Therefore, there is no general loading at object creation.
        self.source = source

    def prefixes(self) -> Dict[str, str]:
        not_supported()

    @abstractmethod
    def types(self) -> List[str]:
        # POLICY Should return managed types in their compacted form (i.e. not IRI nor CURIE).
        pass

    @abstractmethod
    def template(self, type: str, only_required: bool = False) -> Hjson:
        # POLICY Each nested typed resource should have its template included.
        # POLICY Template should be normalized by being sorted so that:
        # - 'type' comes first, compact (i.e. not IRI nor CURIE), recursively,
        # - 'id' comes second, recursively,
        # - properties are sorted alphabetically in their compacted form (i.e. not IRI nor CURIE).
        pass

    def validate(self, data: ManagedData) -> None:
        # POLICY Resource _last_action and _validated should be updated.
        # POLICY Should notify of failures with exception ValidationError including a message.
        # POLICY Should call actions.run() to update the status and deal with exceptions.
        # POLICY Should print Resource _last_action before returning.
        dispatch(data, self._validate_many, self._validate_one)

    @abstractmethod
    def _validate_many(self, resources: Resources) -> None:
        # POLICY Follow validate() policies.
        pass

    @abstractmethod
    def _validate_one(self, resource: Resource) -> None:
        # POLICY Follow validate() policies.
        pass
