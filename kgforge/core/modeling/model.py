from typing import Dict, List, Union

from kgforge.core import Resource, Resources
from kgforge.core.commons.actions import Actions, run
from kgforge.core.commons.attributes import should_be_overridden
from kgforge.core.commons.typing import DirPath, Hjson, ManagedData, URL
from kgforge.core.storing import Store


class Model:

    def __init__(self, source: Union[DirPath, URL, Store]) -> None:
        # FIXME Example.
        # Schemas could be loaded from a directory, an URL, or the store.
        self.source = source

    def prefixes(self) -> Dict[str, str]:
        should_be_overridden()

    def types(self) -> List[str]:
        should_be_overridden()

    def template(self, type: str, only_required: bool = False) -> Hjson:
        # FIXME Example.
        # POLICY Each nested typed resource should have its template included.
        # POLICY Template should be normalized by being sorted so that:
        # - 'type' comes first, recursively,
        # - 'id' comes second, recursively,
        # - properties are sorted alphabetically in their compacted form (i.e. not IRI or CURIE).
        should_be_overridden()

    def validate(self, data: ManagedData) -> None:
        # POLICY Should notify of failures with exceptions extending ValidationError.
        # POLICY Resource._validated should be updated.
        if isinstance(data, Resources):
            return self._validate_many(data)
        else:
            run(self._validate_one, "_validated", data)
            print(data._last_action)

    def _validate_many(self, resources: Resources) -> None:
        # Could be optimized by overriding the method in the specialization.
        for x in resources:
            run(self._validate_one, "_validated", x)
        print(Actions.from_resources(resources))

    def _validate_one(self, resource: Resource) -> None:
        should_be_overridden()


class ValidationError(Exception):

    pass
