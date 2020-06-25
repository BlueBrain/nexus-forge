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
from typing import Any

import requests
from requests import RequestException

from kgforge.core.commons.attributes import repr_class


class Mapping(ABC):

    # See dictionaries.py in kgforge/specializations/mappings/ for a reference implementation.

    # POLICY Exceptions should not be catched so that the KnowledgeGraphForge initialization fails.
    # POLICY Methods of archetypes, except __init__, should not have optional arguments.

    # POLICY Implementations should be declared in kgforge/specializations/mappings/__init__.py.
    # POLICY Implementations should not add methods but private functions in the file.
    # TODO Create a generic parameterizable test suite for mappings. DKE-135.
    # POLICY Implementations should pass tests/specializations/mappings/test_mappings.py.

    def __init__(self, mapping: str) -> None:
        self.rules: Any = self._load_rules(mapping)

    def __repr__(self) -> str:
        return repr_class(self)

    def __str__(self):
        return self._normalize_rules(self.rules)

    def __eq__(self, other: object) -> bool:
        # FIXME To properly work the loading of rules should normalize them. DKE-184.
        # return eq_class(self, other)
        raise NotImplementedError

    @classmethod
    def load(cls, source: str):
        # source: Union[str, FilePath, URL].
        # Mappings could be loaded from a string, a file, or an URL.
        filepath = Path(source)
        if filepath.is_file():
            text = filepath.read_text()
        else:
            try:
                response = requests.get(source)
                response.raise_for_status()
                text = response.text
            except RequestException:
                text = source
        return cls(text)

    def save(self, path: str) -> None:
        # path: FilePath.
        normalized = self._normalize_rules(self.rules)
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(normalized)

    @staticmethod
    @abstractmethod
    def _load_rules(mapping: str) -> Any:
        """Load the mapping rules according to there interpretation."""
        pass

    @staticmethod
    @abstractmethod
    def _normalize_rules(rules: Any) -> str:
        """Normalize the representation of the rules to compare saved mappings."""
        pass
