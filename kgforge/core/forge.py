from typing import Callable

from kgforge.core.modeling import FilesHandler, IdentifiersHandler, ModelingInterface, OntologiesHandler
from kgforge.core.querying import QueryingInterface
from kgforge.core.storing import StoringInterface
from kgforge.core.transforming import TransformingInterface


class KnowledgeGraphForge:

    # FIXME THIS IS NOT THE INTENDED IMPLEMENTATION.
    # FIXME Add necessary arguments.
    def __init__(self) -> None:
        # Interfaces.
        self.modeling = ModelingInterface(self)
        self.querying = QueryingInterface(self)
        self.storing = StoringInterface(self)
        self.transforming = TransformingInterface(self)
        # Handlers.
        self.identifiers = IdentifiersHandler(self)
        self.ontologies = OntologiesHandler(self)
        self.files = FilesHandler(self)

    @staticmethod
    def from_config(path: str, bucket: str, token: str) -> "KnowledgeGraphForge":
        print("FIXME - KnowledgeGraphForge.from_config()")
        return KnowledgeGraphForge()
