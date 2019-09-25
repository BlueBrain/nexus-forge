from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Mapping(ABC):

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
    def load(path: str) -> "Mapping":
        pass

    def save(self, path: str) -> None:
        # POLICY Should save the mapping in a normalized representation.
        normalized = self._normalize_rules(self.rules)
        Path(path).write_text(normalized)

    @abstractmethod
    def _load_rules(self, mapping: str) -> Any:
        pass

    @abstractmethod
    def _normalize_rules(self, rules: Any) -> str:
        pass
