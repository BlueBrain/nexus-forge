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

from typing import Callable, Dict, List

from kgforge.core.commons.typing import ManagedData
from kgforge.core.commons.wrappers import PathsWrapper
from kgforge.core.modeling.model import Model
from kgforge.core.transforming import Mapping
from kgforge.specializations.mappings import DictionaryMapping


class ModelingInterface:

    def __init__(self, model: Model) -> None:
        self.model = model

    def prefixes(self) -> Dict[str, str]:
        return self.model.prefixes()

    def types(self) -> List[str]:
        return self.model.types()

    def template(self, type: str, only_required: bool = False) -> None:
        template = self.model.template(type, only_required)
        print(template)

    def mappings(self, source: str) -> Dict[str, List[str]]:
        return self.model.mappings(source)

    def mapping(self, type: str, source: str, mapping_type: Callable = DictionaryMapping) -> Mapping:
        return self.model.mapping(type, source, mapping_type)

    def validate(self, data: ManagedData) -> None:
        self.model.validate(data)

    def paths(self, type: str) -> PathsWrapper:
        template = self.model.template(type)
        return PathsWrapper._wrap(template)
