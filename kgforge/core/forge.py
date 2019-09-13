from typing import Callable

from kgforge.core.modeling import (FilesHandler, IdentifiersHandler, ModelingInterface,
                                   OntologiesHandler)
from kgforge.core.querying import QueryingInterface
from kgforge.core.storing import StoringInterface
from kgforge.core.transforming import TransformingInterface


class KnowledgeGraphForge:

    # FIXME THIS IS NOT THE INTENDED IMPLEMENTATION.
    # FIXME Add necessary arguments.
    def __init__(self, model: Callable, model_dir: str, store: Callable) -> None:
        # FIXME e.g. model = Neuroshapes. Case from the store.
        # Interfaces.
        self.modeling = ModelingInterface(model, model_dir)
        self.transforming = TransformingInterface(self)
        self.storing = StoringInterface(store)
        self.querying = QueryingInterface(self)
        # Handlers.
        self.identifiers = IdentifiersHandler(self)
        self.ontologies = OntologiesHandler(self)
        self.files = FilesHandler(self)

    @staticmethod
    def from_config(path: str, bucket: str, token: str) -> "KnowledgeGraphForge":
        print("FIXME - KnowledgeGraphForge.from_config()")
        model = eval("Model")
        model_dir = ""
        store = eval("Store")
        return KnowledgeGraphForge(model, model_dir, store)
