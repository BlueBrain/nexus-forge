from abc import ABC, abstractmethod
from pathlib import Path


class Mapping(ABC):

    # TODO Add used versions of the forge and the model.
    # TODO Add used mappings for ontology terms and files.
    # TODO Add used format template for identifiers.

    # See dictionaries.py in kgforge/specializations/mappings for an implementation.

    def __init__(self, mapping: str) -> None:
        # POLICY Should load the mapping according to its interpretation.
        self.rules = self._load_rules(mapping)

    def save(self, path: str) -> None:
        # POLICY Should save the mapping in a normalized representation.
        normalized = self._normalize_rules(self.rules)
        Path(path).write_text(normalized)

    @staticmethod
    @abstractmethod
    def load(path: str):
        pass

    @abstractmethod
    def _load_rules(self, mapping: str):
        pass

    @abstractmethod
    def _normalize_rules(self, rules) -> str:
        pass
