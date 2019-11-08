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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from kgforge.core.commons.typing import FilePath


class Mapping(ABC):

    # TODO Add mapping type.
    # TODO Add used versions of the forge and the model.
    # TODO Add used mappings for ontology terms and files.
    # TODO Add used formatter for identifiers.

    # See dictionaries.py in kgforge/specializations/mappings for an implementation.

    def __init__(self, mapping: str) -> None:
        # POLICY Should load the mapping according to its interpretation.
        self.rules: Any = self._load_rules(mapping)

    def __str__(self):
        return self._normalize_rules(self.rules)

    @staticmethod
    @abstractmethod
    def load(path: FilePath) -> "Mapping":
        pass

    def save(self, path: FilePath) -> None:
        # POLICY Should save the mapping in a normalized representation.
        normalized = self._normalize_rules(self.rules)
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(normalized)

    @abstractmethod
    def _load_rules(self, mapping: str) -> Any:
        pass

    @abstractmethod
    def _normalize_rules(self, rules: Any) -> str:
        pass
