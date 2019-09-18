from typing import Optional, Union

from kgforge.core import Resource, Resources
from kgforge.core.commons.typing import ManagedData


class QueryingInterface:

    def __init__(self, forge) -> None:
        self.forge = forge

    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        return self.forge.store.retrieve(id, version)

    def download(self, data: ManagedData, follow: str, path: str) -> None:
        self.forge.store.download(data, follow, path)

    def search(self, *filters, **params) -> Resources:
        # Accepted parameters: resolving ("exact", "fuzzy"), lookup ("current", "children").
        revolver = self.forge.ontologies.resolve
        return self.forge.store.search(revolver, filters, params)

    def sparql(self, query: str) -> Resources:
        prefixes = self.forge.modeling.prefixes()
        return self.forge.store.sparql(prefixes, query)
