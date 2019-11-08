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

from typing import Union

from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.typing import DirPath, FilePath
from kgforge.core.storing.store import Store


class FilesHandler:

    def __init__(self, store: Store) -> None:
        self._store = store

    def as_resource(self, path: Union[FilePath, DirPath]) -> LazyAction:
        return LazyAction(self._store.upload, path)
