from typing import Callable, Optional, Union

from kgforge.core.commons.typing import DirPath, FilePath, Hjson, URL
from kgforge.core.modeling.interface import ModelingInterface
from kgforge.core.querying.interface import QueryingInterface
from kgforge.core.storing.interface import StoringInterface
from kgforge.core.storing.store import Store
from kgforge.core.transforming.interface import TransformingInterface


class KnowledgeGraphForge:

    # FIXME Implement cases where some of the arguments can be optional.
    def __init__(self,
                 # Model.
                 model: Callable, model_source: Union[DirPath, URL, Store],
                 # Store.
                 store: Callable, files_mapping: Optional[Union[Hjson, FilePath, URL]] = None,
                 bucket: Optional[str] = None, token: Optional[str] = None,
                 # Ontologies.
                 ontologies: Optional[Union[DirPath, URL, Store]] = None,
                 ontologies_mapping: Optional[Union[Hjson, FilePath, URL]] = None,
                 # Identifiers.
                 identifiers_formatter: Optional[str] = None) -> None:
        self.model = model(model_source)
        self.store = store(files_mapping, bucket, token)
        # Handlers.
        # FIXME
        # self.ontologies = OntologiesHandler(ontologies, ontologies_mapping)
        # self.identifiers = IdentifiersHandler(identifiers_formatter)
        # self.files = FilesHandler(self)
        # Interfaces.
        self.modeling = ModelingInterface(self.model)
        self.storing = StoringInterface(self.store)
        self.querying = QueryingInterface(self)
        self.transforming = TransformingInterface(self)

    @staticmethod
    def from_config(path: str, bucket: Optional[str] = None, token: Optional[str] = None) -> "KnowledgeGraphForge":
        # The configuration file is in YAML.
        # FIXME Implement.
        raise NotImplementedError
