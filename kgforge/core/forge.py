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

from __future__ import annotations

import codecs
from copy import deepcopy
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pandas import DataFrame
from poyo import parse_string

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping, Model, OntologyResolver, Store
from kgforge.core.commons.actions import LazyAction
from kgforge.core.conversions.dataframe import as_dataframe, from_dataframe
from kgforge.core.conversions.json import as_json, from_json
from kgforge.core.conversions.jsonld import as_jsonld, from_jsonld
from kgforge.core.conversions.triples import as_triples, from_triples
from kgforge.core.reshaping import Reshaper
from kgforge.core.resolving import ResolvingStrategy
from kgforge.core.wrappings.paths import PathsWrapper, wrap_paths
from kgforge.specializations.mappings import DictionaryMapping


class KnowledgeGraphForge:

    def __init__(self, configuration: Union[str, Dict], bucket: Optional[str] = None,
                 token: Optional[str] = None) -> None:

        # FIXME To be refactored while applying the resolving + mapping API refactoring.

        # The configuration could be provided either as:
        #
        #   - a path to a YAML file with the following structure:
        #     (see demo-forge.yml in kgforge/examples/configurations/ for an example)
        #
        # Model:
        #   name: <a class name in specializations/models, imported in the module __init__.py>  # Required.
        #   source: <a directory path, an URL, or the store name>  # Required.
        #
        # Store:
        #   name: <a class name in specializations/stores, imported in the module __init__.py>  # Required.
        #   endpoint: <an URL>
        #   bucket: <a bucket as a string>
        #   token: <a token as a string>
        #   versioned_id_template: <a string template using 'x' to access resource fields>,
        #   file_resource_mapping: <an Hjson string, a file path, or an URL>
        #
        # Ontologies:
        #   <ontology name>:
        #       source: <a file path, an URL, or the store name>
        #       resolver: <a class name in specializations/resolvers, imported in the module __init__.py>
        #       term_resource_mapping: <an Hjson string, a file path, or an URL>
        #
        # Formatters:
        #   identifier: <a string template with replacement fields delimited by braces, i.e. '{}'>
        #
        #   - a Python dictionary with the following structure:
        #
        # {
        #     "Model": {
        #         "name": <Callable>,  # Required.
        #         "source": <Union[str, Store]>,  # Required.
        #     },
        #     "Store": {
        #         "name": <Callable>>,  # Required.
        #         "endpoint": <str>,
        #         "versioned_id_template": <str>,
        #         "file_resource_mapping": <str>,
        #     },
        #     "Ontologies": {
        #         "name": {
        #             "source": <Union[str, Store]>,
        #             "resolver": <Callable>,
        #             "term_resource_mapping": <str>,
        #         },
        #         ...,
        #     },
        #     "Formatters": {
        #         "<name>": <str>,
        #         ...,
        #     },
        # }
        #

        if isinstance(configuration, str):
            with codecs.open(configuration, encoding="utf-8") as f:
                yaml = f.read()
                config = parse_string(yaml)
        else:
            config = deepcopy(configuration)

        # Model.

        models = import_module("kgforge.specializations.models")
        model_config = config.pop("Model")
        model_name = model_config.pop("name")
        model = getattr(models, model_name)
        self._model: Model = model(**model_config)

        # Store.

        stores = import_module("kgforge.specializations.stores")
        store_config = config.pop("Store")
        store_config.update(bucket=bucket, token=token)
        store_name = store_config.pop("name")
        store = getattr(stores, store_name)
        self._store: Store = store(**store_config)

        # Resolvers.

        # FIXME Planned to be removed while applying the resolving API refactoring.
        def _(ontology: str, conf: Dict) -> OntologyResolver:
            resolver_name = conf.pop("resolver")
            resolver = getattr(resolvers, resolver_name)
            c = {"name": ontology, **conf}
            return resolver(**c)

        if "Ontologies" in config:
            resolvers = import_module("kgforge.specializations.resolvers")
            resolvers_config = config.pop("Ontologies")
            self._resolvers: Dict[str, OntologyResolver] = {k: _(k, v)
                                                            for k, v in resolvers_config.items()}

        # Formatters.

        if "Formatters" in config:
            self._formatters: Dict[str, str] = config.pop("Formatters")

    # Modeling User Interface.

    def prefixes(self) -> Dict[str, str]:
        return self._model.prefixes()

    def types(self) -> List[str]:
        return self._model.types()

    def template(self, type: str, only_required: bool = False) -> None:
        template = self._model.template(type, only_required)
        print(template)

    def validate(self, data: Union[Resource, List[Resource]]) -> None:
        self._model.validate(data)

    # Resolving User Interface.

    # FIXME To be refactored while applying the resolving API refactoring.
    def resolve(self, label: str, ontology: str, type: str = "Class",
                strategy: ResolvingStrategy = ResolvingStrategy.BEST_MATCH) -> Union[Resource, List[Resource]]:
        resolver = self._resolvers[ontology]
        return resolver.resolve(label, type, strategy)

    # Formatting User Interface.

    def format(self, what: str, *args) -> str:
        return self._formatters[what].format(*args)

    # Mapping User Interface.

    # FIXME To be refactored while applying the mapping API refactoring.
    def mappings(self, source: str) -> Dict[str, List[str]]:
        return self._model.mappings(source)

    # FIXME To be refactored while applying the mapping API refactoring.
    def mapping(self, type: str, source: str,
                mapping_type: Callable = DictionaryMapping) -> Mapping:
        return self._model.mapping(type, source, mapping_type)

    def map(self, data: Any, mapper: Callable,
            mapping: Mapping) -> Union[Resource, List[Resource]]:
        # There is no need to cache mappers as for collections map() is directly called on them.
        return mapper(self).map(data, mapping)

    # Reshaping User Interface.

    def reshape(self, data: Union[Resource, List[Resource]], keep: List[str],
                versioned: bool = False) -> Union[Resource, List[Resource]]:
        return Reshaper(self._store.versioned_id_template).reshape(data, keep, versioned)

    # Querying User Interface.

    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        return self._store.retrieve(id, version)

    def paths(self, type: str) -> PathsWrapper:
        template = self._model.template(type, False)
        return wrap_paths(template)

    def search(self, *filters, **params) -> List[Resource]:
        resolvers = list(self._resolvers.values())
        return self._store.search(resolvers, *filters, **params)

    def sparql(self, query: str) -> List[Resource]:
        prefixes = self._model.prefixes()
        return self._store.sparql(prefixes, query)

    def download(self, data: Union[Resource, List[Resource]], follow: str, path: str) -> None:
        # path: DirPath.
        self._store.download(data, follow, path)

    # Storing User Interface.

    def register(self, data: Union[Resource, List[Resource]]) -> None:
        self._store.register(data)

    def update(self, data: Union[Resource, List[Resource]]) -> None:
        self._store.update(data)

    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        self._store.deprecate(data)

    # Versioning User Interface.

    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        self._store.tag(data, value)

    def freeze(self, data: Union[Resource, List[Resource]]) -> None:
        self._store.freeze(data)

    # Files Handling User Interface.

    def attach(self, path: str) -> LazyAction:
        # path: Union[FilePath, DirPath].
        return LazyAction(self._store.upload, path)

    # Converting User Interface.

    @staticmethod
    def as_json(data: Union[Resource, List[Resource]], expanded: bool = False,
                store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return as_json(data, expanded, store_metadata)

    @staticmethod
    def as_jsonld(data: Union[Resource, List[Resource]], compacted: bool = True,
                  store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return as_jsonld(data, compacted, store_metadata)

    # FIXME To be refactored after the introduction of as_graph(), as_rdf() and as_triplets().
    @staticmethod
    def as_triples(data: Union[Resource, List[Resource]],
                   store_metadata: bool = False) -> List[Tuple[str, str, str]]:
        return as_triples(data, store_metadata)

    @staticmethod
    def as_dataframe(data: List[Resource], store_metadata: bool = False, na: Optional[str] = None,
                     nesting: str = ".") -> DataFrame:
        return as_dataframe(data, store_metadata, na, nesting)

    @staticmethod
    def from_json(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]:
        return from_json(data)

    @staticmethod
    def from_jsonld(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]:
        return from_jsonld(data)

    @staticmethod
    def from_triples(data: List[Tuple[str, str, str]]) -> Union[Resource, List[Resource]]:
        return from_triples(data)

    @staticmethod
    def from_dataframe(data: DataFrame, na: Optional[str] = None,
                       nesting: str = ".") -> List[Resource]:
        return from_dataframe(data, na, nesting)
