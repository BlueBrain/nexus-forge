import random
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

from kgforge.core import Resource, Resources
from kgforge.core.commons.typing import ManagedData
from kgforge.core.modeling.handlers.ontologies import OntologyResolver
from kgforge.core.storing import Store
from kgforge.specializations.mappers import DictionaryMapper


class ResourceAlreadyExists(RegistrationError):

    pass


class DemoStore(Store):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("DEMO - DemoStore")
        self._data = {}

    # [C]RUD

    def _register_one(self, resource: Resource, update: bool = False) -> None:

        run(self._register_one, "_synchronized", resource, update=update)
        print(resource._last_action)

        print("DEMO - DemoStore.register_one()")
        if update:
            stored = self._data[resource.id]
            new_rev = len(stored) + 1
            resource._store_metadata["rev"] = new_rev
            self._data[resource.id] = stored.append(resource)
        else:
            if resource.id in self._data:
                raise ResourceAlreadyExists
            else:
                resource._store_metadata = {"rev": 1}
                self._data[resource.id] = [resource]

    def _upload_one(self, filepath: Path) -> Resource:
        print("DEMO - DemoStore.upload_one()")
        uploaded = {
            "type": "File",
            "id": f"https://bbp.epfl.ch/neurosciencegraph/data/{str(uuid4())}",
            "_bytes": random.randint(1000, 10000),
            "_filename": filepath.name,
            "_mediaType": "application/octet-stream",
        }
        return DictionaryMapper(None).map(uploaded, self.files_mapping)

    # C[R]UD

    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        print("DEMO - DemoStore.retrieve()")

    def download(self, data: ManagedData, follow: str, path: str) -> None:
        print("DEMO - DemoStore.download()")

    # CR[U]D

    def tag(self, data: ManagedData, value: str) -> None:
        print("DEMO - DemoStore.tag_version()")

    # CRU[D]

    def deprecate(self, data: ManagedData) -> None:
        pass

    # Query

    def search(self, resolver: OntologyResolver, *filters, **params) -> Resources:
        print("DEMO - DemoStore.search()")
        for x in params:
            not_supported(x, "DemoStore")
        results = [v[-1] for _, v in self._data.items()]
        for x in filters:
            # FIXME Demo for path with elements to resolve.
            # path = ".".join(resolver.resolve("object property", x) for x in x.path)
            path = ".".join(x.path)
            results = [y for y in results if eval(f"y.{path}.{x.operator}({x.value})")]
        return Resources(results)

    def sparql(self, query: str) -> Resources:
        pass

    # Versioning

    def freeze(self, resource: Resource) -> None:
        pass
