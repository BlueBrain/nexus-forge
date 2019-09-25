import codecs
from importlib import import_module
from typing import Callable, Dict, List, Optional, Union

from poyo import parse_string

from kgforge.core.commons.typing import DirPath, FilePath, Hjson, URL
from kgforge.core.modeling import Model
from kgforge.core.modeling.handlers.files import FilesHandler
from kgforge.core.modeling.handlers.identifiers import IdentifiersHandler
from kgforge.core.modeling.handlers.ontologies import OntologiesHandler
from kgforge.core.modeling.interface import ModelingInterface
from kgforge.core.modeling.resolvers import OntologyConfiguration
from kgforge.core.querying.interface import QueryingInterface
from kgforge.core.storing import Store
from kgforge.core.storing.interface import StoringInterface
from kgforge.core.transforming.interface import TransformingInterface


class KnowledgeGraphForge:

    def __init__(self,
                 # Model.
                 model: Callable,
                 model_source: Union[DirPath, URL, "Store"],
                 # Store.
                 store: Callable,
                 files_mapping: Optional[Union[Hjson, FilePath, URL]] = None,
                 bucket: Optional[str] = None,
                 token: Optional[str] = None,
                 # Ontologies.
                 ontologies: Optional[List[OntologyConfiguration]] = None,
                 # Identifiers.
                 formatter: Optional[str] = None) -> None:
        self.model: Model = model(model_source)
        self.store: Store = store(files_mapping, bucket, token)
        # Handlers.
        self.ontologies = OntologiesHandler(ontologies) if ontologies else None
        self.identifiers = IdentifiersHandler(formatter) if formatter else None
        self.files = FilesHandler(self.store)
        # Interfaces.
        self.modeling = ModelingInterface(self.model)
        self.storing = StoringInterface(self.store)
        self.querying = QueryingInterface(self)
        self.transforming = TransformingInterface(self)

    @staticmethod
    def from_config(path: str, bucket: Optional[str] = None, token: Optional[str] = None) -> "KnowledgeGraphForge":
        # POLICY The configuration file is in YAML and has the following structure.
        # See demo-forge.yml in examples/ for an example.
        #
        # Model:
        #   name: <a class name in specializations/models, imported in the module __init__.py>
        #   source: <a directory path, an URL, or the model name>
        #
        # Store:
        #   name: <a class name in specializations/stores, imported in the module __init__.py>
        #   files mapping: <an Hjson string, a file path, or an URL>  # (optional)
        #
        # (optional)
        # Ontologies:
        #   <ontology name>:
        #       source: <a file path, an URL, or the store name>
        #       terms mapping: <an Hjson string, a file path, or an URL>
        #       resolver: <a class name in specializations/resolvers, imported in the module __init__.py>
        #
        # (optional)
        # Identifiers:
        #   formatter: <a string with replacement fields delimited by braces, i.e. '{}'>
        #
        def _convert(configurations: Dict) -> List[OntologyConfiguration]:
            return [OntologyConfiguration(name=k, source=v["source"], terms_mapping=v["terms mapping"],
                                          resolver=getattr(resolvers, v["resolver"]))
                    for k, v in configurations.items()]
        models = import_module("kgforge.specializations.models")
        stores = import_module("kgforge.specializations.stores")
        resolvers = import_module("kgforge.specializations.resolvers")
        with codecs.open(path, encoding="utf-8") as f:
            yaml = f.read()
            config = parse_string(yaml)
            # Model.
            model = getattr(models, config["Model"]["name"])
            model_source = config["Model"]["source"]
            # Store.
            store = getattr(stores, config["Store"]["name"])
            files_mapping = config["Store"].get("files mapping", None)
            # Ontologies.
            configurations = config.get("Ontologies", None)
            ontologies = _convert(configurations) if configurations else None
            # Identifiers.
            formatter = config.get("Identifiers", {}).get("formatter", None)
            return KnowledgeGraphForge(model, model_source, store, files_mapping, bucket, token,
                                       ontologies, formatter)
