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

import codecs
from importlib import import_module
from typing import Callable, Dict, Optional, Union

from poyo import parse_string

from kgforge.core.commons.typing import DirPath, URL
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

    def __init__(self, model: Callable, model_source: Union[DirPath, URL, "Store"], store: Callable, **kwargs) -> None:
        # Accepted parameters:
        #   > Store:
        #       - endpoint: URL
        #       - bucket: str
        #       - token: str
        #       - file_resource_mapping: Union[Hjson, FilePath, URL]
        #   > Ontologies
        #       - ontologies: List[OntologyConfiguration]
        #   > Identifiers
        #       - formatter: str
        # Model.
        self._model: Model = model(model_source)
        # Store.
        self._store: Store = store(**kwargs)
        # Handlers.
        self.ontologies = OntologiesHandler(kwargs["ontologies"]) if "ontologies" in kwargs else None
        self.identifiers = IdentifiersHandler(kwargs["formatter"]) if "formatter" in kwargs else None
        self.files = FilesHandler(self._store)
        # Interfaces.
        self.modeling = ModelingInterface(self._model)
        self.storing = StoringInterface(self._store)
        self.querying = QueryingInterface(self)
        self.transforming = TransformingInterface(self)

    @staticmethod
    def from_config(path: str, bucket: Optional[str] = None, token: Optional[str] = None) -> "KnowledgeGraphForge":
        # POLICY The configuration file is in YAML and has the following structure.
        # See demo-forge.yml in examples/ for an example.
        #
        # Model:
        #   name: <a class name in specializations/models, imported in the module __init__.py>
        #   source: <a directory path, an URL, or the store name>
        #
        # Store:
        #   name: <a class name in specializations/stores, imported in the module __init__.py>
        #   endpoint: <an URL>  # (optional)
        #   file_resource_mapping: <an Hjson string, a file path, or an URL>  # (optional)
        #
        # (optional)
        # TODO Add possibility to configure default resolver and term_resource_mapping.
        # Ontologies:
        #   <ontology name>:
        #       source: <a file path, an URL, or the store name>
        #       resolver: <a class name in specializations/resolvers, imported in the module __init__.py>
        #       term_resource_mapping: <an Hjson string, a file path, or an URL>
        #
        # (optional)
        # Identifiers:
        #   formatter: <a string with replacement fields delimited by braces, i.e. '{}'>

        def load_onto_config(name, x: Dict) -> OntologyConfiguration:
            resolver = getattr(resolvers, x["resolver"])
            return OntologyConfiguration(name, x["source"], resolver, x["term_resource_mapping"])

        models = import_module("kgforge.specializations.models")
        stores = import_module("kgforge.specializations.stores")
        resolvers = import_module("kgforge.specializations.resolvers")

        with codecs.open(path, encoding="utf-8") as f:
            yaml = f.read()
            config = parse_string(yaml)
            model_name = config["Model"].pop("name")
            model_source = config["Model"].pop("source")
            store_name = config["Store"].pop("name")
            kwargs = {**config["Store"]}
            if "Ontologies" in config:
                configurations = [load_onto_config(k, v) for k, v in config["Ontologies"].items()]
                kwargs.update(ontologies=configurations)
            if "Identifiers" in config:
                kwargs.update(config["Identifiers"])
            return KnowledgeGraphForge(model=getattr(models, model_name), model_source=model_source,
                                       store=getattr(stores, store_name), bucket=bucket, token=token,
                                       **kwargs)
