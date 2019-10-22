# 
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Union

from kgforge.core.commons.typing import ManagedData
from kgforge.core.resources import Resource, Resources


class QueryingInterface:

    def __init__(self, forge: "KnowledgeGraphForge") -> None:
        self.forge = forge

    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        return self.forge._store.retrieve(id, version)

    def search(self, *filters, **params) -> Resources:
        revolvers = self.forge.ontologies
        return self.forge._store.search(revolvers, *filters, **params)

    def sparql(self, query: str) -> Resources:
        prefixes = self.forge.modeling.prefixes()
        return self.forge._store.sparql(prefixes, query)

    def download(self, data: ManagedData, follow: str, path: str) -> None:
        self.forge._store.download(data, follow, path)
