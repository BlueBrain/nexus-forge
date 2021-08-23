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

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import yaml
from kgforge.core.commons.files import load_file_as_byte
from pandas import DataFrame
from rdflib import Graph

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping, Model, Resolver, Store
from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.dictionaries import with_defaults
from kgforge.core.commons.exceptions import ResolvingError
from kgforge.core.commons.execution import catch
from kgforge.core.commons.imports import import_class
from kgforge.core.commons.strategies import ResolvingStrategy
from kgforge.core.conversions.dataframe import as_dataframe, from_dataframe
from kgforge.core.conversions.json import as_json, from_json
from kgforge.core.conversions.rdf import as_jsonld, from_jsonld, as_graph, from_graph, Form
from kgforge.core.reshaping import Reshaper
from kgforge.core.wrappings.paths import PathsWrapper, wrap_paths
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping


class KnowledgeGraphForge:

    # POLICY Class name should be imported in the corresponding module __init__.py.

    # No catching of exceptions so that no incomplete instance is created if an error occurs.
    # This is a best practice in Python for __init__().
    def __init__(self, configuration: Union[str, Dict], **kwargs) -> None:

        # Required minimal configuration: name for Model and Store, origin and source for Model.
        # Keyword arguments could be used to override the configuration provided for the Store.
        #
        # The configuration could be provided either as:
        #
        #   - A path to a YAML file with the following structure.
        #     Class name could be provided in three formats:
        #       * 'SomeClass',
        #       * 'SomeClass from package.module',
        #       * 'SomeClass from package.module.file'.
        #     When the class is from this package, the first is used. Otherwise, the two others.
        #     Values using braces with something inside should be quoted with double quotes.
        #     See demo-forge.yml in kgforge/examples/configurations/ for an example.
        #
        # Model:
        #   name: <a class name of a Model>
        #   origin: <'directory', 'url', or 'store'>
        #   source: <a directory path, an URL, or the class name of a Store>
        #   bucket: <when 'origin' is 'store', a Store bucket>
        #   endpoint: <when 'origin' is 'store', a Store endpoint, default to Store:endpoint>
        #   token: <when 'origin' is 'store', a Store token, default to Store:token>
        #   context:
        #     iri: <an IRI>
        #     bucket: <when 'origin' is 'store', a Store bucket, default to Model:bucket>
        #     endpoint: <when 'origin' is 'store', a Store endpoint, default to Model:endpoint>
        #     token: <when 'origin' is 'store', a Store token, default to Model:token>
        #
        # Store:
        #   name: <a class name of a Store>
        #   endpoint: <an URL>
        #   bucket: <a bucket as a string>
        #   token: <a token as a string>
        #   searchendpoints:
        #     <querytype>: <a query paradigm supported by configured store (e.g. sparql)>
        #       endpoint: <an IRI of a query endpoint>
        #   versioned_id_template: <a string template using 'x' to access resource fields>
        #   file_resource_mapping: <an Hjson string, a file path, or an URL>
        #
        # Resolvers:
        #   <scope>:
        #     - resolver: <a class name of a Resolver>
        #       origin: <'directory', 'web_service', or 'store'>
        #       source: <a directory path, a web service endpoint, or the class name of a Store>
        #       targets:
        #         - identifier: <a name, or an IRI>
        #           bucket: <a file name, an URL path, or a Store bucket>
        #       result_resource_mapping: <an Hjson string, a file path, or an URL>
        #       endpoint: <when 'origin' is 'store', a Store endpoint, default to Store:endpoint>
        #       token: <when 'origin' is 'store', a Store token, default to Store:token>
        #
        # Formatters:
        #   <identifier>: <a string template with replacement fields delimited by braces, i.e. '{}'>
        #
        #   - A Python dictionary with the following structure.
        #
        # {
        #     "Model": {
        #         "name": <str>,
        #         "origin": <str>,
        #         "source": <str>,
        #         "bucket": <str>,
        #         "endpoint": <str>,
        #         "token": <str>,
        #         "context": {
        #               "iri": <str>,
        #               "bucket": <str>,
        #               "endpoint": <str>,
        #               "token": <str>,
        #         }
        #     },
        #     "Store": {
        #         "name": <str>,
        #         "endpoint": <str>,
        #         "bucket": <str>,
        #         "token": <str>,
        #         "searchendpoints": {
        #           "<querytype>": {
        #               "endpoint": <str>
        #           }
        #         }
        #         "versioned_id_template": <str>,
        #         "file_resource_mapping": <str>,
        #     },
        #     "Resolvers": {
        #         "<scope>": [
        #             {
        #                 "resolver": <str>,
        #                 "origin": <str>,
        #                 "source": <str>,
        #                 "targets": [
        #                     {
        #                         "identifier": <str>,
        #                         "bucket": <str>,
        #                     },
        #                     ...,
        #                 ],
        #                 "result_resource_mapping": <str>,
        #                 "endpoint": <str>,
        #                 "token": <str>,
        #             },
        #             ...,
        #         ],
        #     },
        #     "Formatters": {
        #         "<name>": <str>,
        #         ...,
        #     },
        # }
        if isinstance(configuration, str):
            config_data = load_file_as_byte(configuration)
            config_data = config_data.decode("utf-8")
            config = yaml.safe_load(config_data)
        else:
            config = deepcopy(configuration)

        # Debugging.
        self._debug = kwargs.pop("debug", False)

        # Store.
        store_config = config.pop("Store")
        store_config.update(kwargs)

        # Model.
        model_config = config.pop("Model")
        if model_config["origin"] == "store":
            with_defaults(model_config, store_config, "source", "name", ["endpoint", "token", "bucket", "vocabulary"])
        model_name = model_config.pop("name")
        model = import_class(model_name, "models")
        self._model: Model = model(**model_config)

        # Store.

        store_config.update(model_context=self._model.context())
        store_name = store_config.pop("name")
        store = import_class(store_name, "stores")
        self._store: Store = store(**store_config)
        store_config.update(name=store_name)

        # Resolvers.
        resolvers_config = config.pop("Resolvers", None)
        # Format: Optional[Dict[scope_name, Dict[resolver_name, Resolver]]].
        self._resolvers: Optional[Dict[str, Dict[str, Resolver]]] = prepare_resolvers(
            resolvers_config, store_config) if resolvers_config else None

        # Formatters.
        self._formatters: Optional[Dict[str, str]] = config.pop("Formatters", None)

    # Modeling User Interface.

    @catch
    def prefixes(self, pretty: bool = True) -> Optional[Dict[str, str]]:
        return self._model.prefixes(pretty)

    @catch
    def types(self, pretty: bool = True) -> Optional[List[str]]:
        return self._model.types(pretty)

    @catch
    def template(self, type: str, only_required: bool = False, output: str = "hjson"
                 ) -> Optional[Dict]:
        return self._model.template(type, only_required, output)

    # No @catch because the error handling is done by execution.run().
    def validate(self, data: Union[Resource, List[Resource]],
                 execute_actions_before: bool = False) -> None:
        self._model.validate(data, execute_actions_before)

    # Resolving User Interface.

    def resolvers(self):
        print("Available scopes:")
        for k, v in sorted(self._resolvers.items()):
            print(" - ", k, ":")
            for r_key, r_value in v.items():
                print("     - resolver: ", r_key)
                print("         - targets: ",  ",".join(r_value.targets.keys()))

    @catch
    def resolve(self, text: Union[str, List[str], Resource], scope: Optional[str] = None, resolver: Optional[str] = None,
                target: Optional[str] = None, type: Optional[str] = None,
                strategy: Union[ResolvingStrategy, str] = ResolvingStrategy.BEST_MATCH,
                resolving_context: Optional[Any] = None, property_to_resolve: Optional[str] = None,
                merge_inplace_as: Optional[str] = None,
                limit: Optional[int] = 10, threshold: Optional[float] = 0.5) \
            -> Optional[Union[Resource, List[Resource], Dict[str, List[Resource]]]]:
        """
        Resolve a string into a existing resource or list of resources depending on the resolving
        strategy

        Args:
            text (Union[str, List[str], Resource]): string(s) to resolve.
            scope (str): a scope identifier
            resolver (str): a resolver name
            target (str): an identifier in the targets
            type (str): a Type to be used as part of the query
            strategy (str): a ResolvingStrategy.[ALL_MATCHES, BEST_MATCH, EXACT_MATCH]
            resolving_context: the context (e.g surrounding words in a paragraph) of the text to resolve
            property_to_resolve: the resource's attribute to get text to resolve from in case provided text is a Resource
            merge_inplace_as: the resource's attribute to merge the resolve reesult in when the provided text is a Resource
            limit (int): the maximum number of results to return when using ALL_MATCHES, default is 10
            threshold (float): the maximum (if the score is a distance) or minimum (if the score is a similarity) score value for each result, default is 0.8
        Returns:
            resources (Resource, List(Resource), Dict[str, List[Resource]])
        """
        if self._resolvers is not None:
            if scope is not None and scope in self._resolvers:
                if resolver is not None:
                    rov = self._resolvers[scope][resolver]
                else:
                    scope_resolvers = list(self._resolvers[scope].values())
                    if len(scope_resolvers) == 1:
                        rov = scope_resolvers[0]
                    else:
                        raise ResolvingError("resolver name should be specified")
            elif scope is not None:
                raise AttributeError(f"{scope} is not a configured resolving scope. Configured scopes are {list(self._resolvers.keys())}")
            else:
                scopes_resolvers = list(self._resolvers.values())
                if resolver is not None:
                    if len(self._resolvers) == 1:
                        rov = scopes_resolvers[0][resolver]
                    else:
                        raise ResolvingError("resolving scope should be specified in case of multiple available resolvers")
                else:
                    if len(self._resolvers) == 1 and len(scopes_resolvers[0]) == 1:
                        rov = list(scopes_resolvers[0].values())[0]
                    else:
                        raise ResolvingError("resolving scope or resolver name should be "
                                             "specified in case of multiple available resolvers")
            try:
                strategy = strategy if isinstance(strategy, ResolvingStrategy) else ResolvingStrategy[strategy]
            except Exception as e:
                raise AttributeError(f"Invalid ResolvingStrategy value '{strategy}'. Allowed names are {[name for name, member in ResolvingStrategy.__members__.items()]} and allowed members are {[member for name, member in ResolvingStrategy.__members__.items()]}")
            return rov.resolve(text, target, type, strategy, resolving_context, property_to_resolve, merge_inplace_as,
                               limit, threshold)
        else:
            raise ResolvingError("no resolvers have been configured")

    # Formatting User Interface.

    @catch
    def format(self, what: str, *args) -> str:
        return self._formatters[what].format(*args)

    # Mapping User Interface.

    @catch
    def sources(self, pretty: bool = True) -> Optional[List[str]]:
        return self._model.sources(pretty)

    @catch
    def mappings(self, source: str, pretty: bool = True) -> Optional[Dict[str, List[str]]]:
        return self._model.mappings(source, pretty)

    @catch
    def mapping(self, entity: str, source: str, type: Callable = DictionaryMapping) -> Mapping:
        return self._model.mapping(entity, source, type)

    @catch
    def map(self, data: Any, mapping: Union[Mapping, List[Mapping]],
            mapper: Callable = DictionaryMapper, na: Union[Any, List[Any]] = None
            ) -> Union[Resource, List[Resource]]:
        return mapper(self).map(data, mapping, na)

    # Reshaping User Interface.

    @catch
    def reshape(self, data: Union[Resource, List[Resource]], keep: List[str],
                versioned: bool = False) -> Union[Resource, List[Resource]]:
        return Reshaper(self._store.versioned_id_template).reshape(data, keep, versioned)

    # Querying User Interface.

    @catch
    def retrieve(self, id: str, version: Optional[Union[int, str]] = None,
                 cross_bucket: bool = False) -> Resource:
        return self._store.retrieve(id, version, cross_bucket)

    @catch
    def paths(self, type: str) -> PathsWrapper:
        template = self._model.template(type, False, "dict")
        return wrap_paths(template)

    @catch
    def search(self, *filters, **params) -> List[Resource]:
        resolvers = list(self._resolvers.values()) if self._resolvers is not None else None
        return self._store.search(resolvers, *filters, **params)

    @catch
    def sparql(self, query: str, debug: bool = False, limit: int = 100,
               offset: Optional[int] = None) -> List[Resource]:
        return self._store.sparql(query, debug, limit, offset)

    @catch
    def elastic(self, query: str, debug: bool = False, limit: int = 100, offset: Optional[int] = None)\
            -> List[Resource]:
        return self._store.elastic(query, debug, limit, offset)

    @catch
    def download(self, data: Union[Resource, List[Resource]], follow: str, path: str,
                 overwrite: bool = False, cross_bucket: bool = False) -> None:
        # path: DirPath.
        self._store.download(data, follow, path, overwrite, cross_bucket)

    # Storing User Interface.

    # No @catch because the error handling is done by execution.run().
    def register(self, data: Union[Resource, List[Resource]], schema_id: Optional[str]=None) -> None:
        self._store.register(data, schema_id)

    # No @catch because the error handling is done by execution.run().
    def update(self, data: Union[Resource, List[Resource]], schema_id: Optional[str] = None) -> None:
        self._store.update(data, schema_id)

    # No @catch because the error handling is done by execution.run().
    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        self._store.deprecate(data)

    # Versioning User Interface.

    # No @catch because the error handling is done by execution.run().
    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        self._store.tag(data, value)

    # No @catch because the error handling is done by execution.run().
    def freeze(self, data: Union[Resource, List[Resource]]) -> None:
        self._store.freeze(data)

    # Files Handling User Interface.

    @catch
    def attach(self, path: str, content_type: str = None) -> LazyAction:
        # path: Union[FilePath, DirPath].
        return LazyAction(self._store.upload, path, content_type)

    # Converting User Interface.

    @catch
    def as_json(self, data: Union[Resource, List[Resource]], expanded: bool = False,
                store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return as_json(data, expanded, store_metadata, self._model.context(),
                       self._store.metadata_context, self._model.resolve_context)

    @catch
    @catch
    def as_jsonld(self, data: Union[Resource, List[Resource]], form: str = Form.COMPACTED.value,
                  store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        return as_jsonld(data, form, store_metadata, self._model.context(),
                         self._store.metadata_context, self._model.resolve_context, None)

    @catch
    def as_graph(self, data: Union[Resource, List[Resource]], store_metadata: bool = False) -> Graph:
        return as_graph(data, store_metadata, self._model.context(), self._store.metadata_context,
                        self._model.resolve_context)

    @catch
    def as_dataframe(self, data: Union[Resource, List[Resource]], na: Union[Any, List[Any]] = [None], nesting: str = ".",
                     expanded: bool = False, store_metadata: bool = False) -> DataFrame:
        return as_dataframe(data, na, nesting, expanded, store_metadata, self._model.context(),
                            self._store.metadata_context, self._model.resolve_context)

    @catch
    def from_json(self, data: Union[Dict, List[Dict]], na: Union[Any, List[Any]] = None
                  ) -> Union[Resource, List[Resource]]:
        return from_json(data, na)

    @catch
    def from_jsonld(self, data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]:
        return from_jsonld(data)

    @catch
    def from_graph(self, data: Graph, type: Union[str, List[str]] = None,
                   frame: Dict = None, use_model_context=False) -> Union[Resource, List[Resource]]:
        context = self._model.context() if use_model_context else None
        return from_graph(data, type, frame, context)

    @catch
    def from_dataframe(self, data: DataFrame, na: Union[Any, List[Any]] = np.nan,
                       nesting: str = ".") -> Union[Resource, List[Resource]]:
        return from_dataframe(data, na, nesting)


def prepare_resolvers(config: Dict, store_config: Dict) -> Dict[str, Dict[str, Resolver]]:
    return {scope: dict(prepare_resolver(x, store_config) for x in configs)
            for scope, configs in config.items()}


def prepare_resolver(config: Dict, store_config: Dict) -> Tuple[str, Resolver]:
    if config["origin"] == "store":
        with_defaults(config, store_config, "source", "name", ["endpoint", "token", "bucket", "model_context",
                                                               "searchendpoints", "vocabulary"])
    resolver_name = config.pop("resolver")
    resolver = import_class(resolver_name, "resolvers")
    return resolver.__name__, resolver(**config)
