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

from kgforge.core.commons.typing import ManagedData
from kgforge.core.storing.store import Store


class StoringInterface:

    def __init__(self, store: Store) -> None:
        self._store: Store = store

    def register(self, data: ManagedData) -> None:
        self._store.register(data, update=False)

    def update(self, data: ManagedData) -> None:
        self._store.update(data)

    def tag(self, data: ManagedData, value: str) -> None:
        self._store.tag(data, value)

    def deprecate(self, data: ManagedData) -> None:
        self._store.deprecate(data)
