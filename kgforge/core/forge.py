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
from kgforge.core.conversions.rdf import (
    as_jsonld,
    from_jsonld,
    as_graph,
    from_graph,
    Form,
)
from kgforge.core.reshaping import Reshaper
from kgforge.core.wrappings.paths import PathsWrapper, wrap_paths
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping


class KnowledgeGraphForge:

    # POLICY Class name should be imported in the corresponding module __init__.py.

    # No catching of exceptions so that no incomplete instance is created if an error occurs.
    # This is a best practice in Python for __init__().
    def __init__(self, configuration: Union[str, Dict], **kwargs) -> None:
        """
        Configure and create a Knowledge Graph forge session.
        See https://github.com/BlueBrain/nexus-forge/blob/master/examples/notebooks/use-cases/prod-forge-nexus.yml for an example of configuration.

        Required minimal configuration: name, origin and source for Model and name for Store.
        Keyword arguments could be used to override the configuration provided for the Store.

        The configuration could be provided either as:

        - inline YAML or a path to a YAML file with the following structure:

         Model:
           name: <a class name of a Model>
           origin: <'directory', 'url', or 'store'>
           source: <a directory path, an URL, or the class name of a Store>
           bucket: <when 'origin' is 'store', a Store bucket>
           endpoint: <when 'origin' is 'store', a Store endpoint, default to Store:endpoint>
           token: <when 'origin' is 'store', a Store token, default to Store:token>
           context:
             iri: <an IRI>
             bucket: <when 'origin' is 'store', a Store bucket, default to Model:bucket>
             endpoint: <when 'origin' is 'store', a Store endpoint, default to Model:endpoint>
             token: <when 'origin' is 'store', a Store token, default to Model:token>

         Store:
           name: <a class name of a Store>
           endpoint: <an URL>
           bucket: <a bucket as a string>
           token: <a token as a string>
           searchendpoints:
             <querytype>: <a query paradigm supported by configured store (e.g. sparql)>
               endpoint: <an IRI of a query endpoint>
           params:
               <Store method>: <e.g. register, tag, ...>
                   param: <http query param value to use for the Store method>
           versioned_id_template: <a string template using 'x' to access resource fields>
           file_resource_mapping: <an Hjson string, a file path, or an URL>

         Resolvers:
           <scope>:
             - resolver: <a class name of a Resolver>
               origin: <'directory', 'web_service', or 'store'>
               source: <a directory path, a web service endpoint, or the class name of a Store>
               targets:
                 - identifier: <a name, or an IRI>
                   bucket: <a file name, an URL path, or a Store bucket>
               result_resource_mapping: <an Hjson string, a file path, or an URL>
               endpoint: <when 'origin' is 'store', a Store endpoint, default to Store:endpoint>
               token: <when 'origin' is 'store', a Store token, default to Store:token>

         Formatters:
           <identifier>: <a string template with replacement fields delimited by braces, i.e. '{}'>

        - A Python dictionary with the following structure:

         {
             "Model": {
                 "name": <str>,
                 "origin": <str>,
                 "source": <str>,
                 "bucket": <str>,
                 "endpoint": <str>,
                 "token": <str>,
                 "context": {
                       "iri": <str>,
                       "bucket": <str>,
                       "endpoint": <str>,
                       "token": <str>,
                 }
             },
             "Store": {
                 "name": <str>,
                 "endpoint": <str>,
                 "bucket": <str>,
                 "token": <str>,
                 "searchendpoints": {
                   "<querytype>": {
                       "endpoint": <str>
                   }
                 },
                 "params": {
                   "<Store method>": {
                       "param": <str>
                   }
                 },
                 "versioned_id_template": <str>,
                 "file_resource_mapping": <str>,
             },
             "Resolvers": {
                 "<scope>": [
                     {
                         "resolver": <str>,
                         "origin": <str>,
                         "source": <str>,
                         "targets": [
                             {
                                 "identifier": <str>,
                                 "bucket": <str>,
                             },
                             ...,
                         ],
                         "result_resource_mapping": <str>,
                         "endpoint": <str>,
                         "token": <str>,
                     },
                     ...,
                 ],
             },
             "Formatters": {
                 "<name>": <str>,
                 ...,
             },
         }

         In the configuration, Class name could be provided in three formats:
               * 'SomeClass',
               * 'SomeClass from package.module',
               * 'SomeClass from package.module.file'.
         When the class is from this package, the first is used. Otherwise, the two others.
         Values using braces with something inside should be quoted with double quotes.

        :param configuration: a configuration content or file path
        :param kwargs:  keyword arguments
        """

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
            with_defaults(
                model_config,
                store_config,
                "source",
                "name",
                ["endpoint", "token", "bucket", "vocabulary"],
            )
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
        self._resolvers: Optional[Dict[str, Dict[str, Resolver]]] = (
            prepare_resolvers(resolvers_config, store_config)
            if resolvers_config
            else None
        )

        # Formatters.
        self._formatters: Optional[Dict[str, str]] = config.pop("Formatters", None)

    # Modeling User Interface.

    @catch
    def prefixes(self, pretty: bool = True) -> Optional[Dict[str, str]]:
        """
        Print (pretty=True) prefix mappings:
            Used prefixes:
            rdf          http://www.w3.org/1999/02/22-rdf-syntax-ns#
            prov         http://www.w3.org/ns/prov#

        Or return (pretty=False) them as dictionary:
            {
                "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "prov":"http://www.w3.org/ns/prov#"
            }

        :param pretty: a boolean
        :return: Optional[Dict[str, str]]
        """
        return self._model.prefixes(pretty)

    @catch
    def types(self, pretty: bool = True) -> Optional[List[str]]:
        """
        Print (pretty=True) known resource types (by the configured Model):

        Managed entity types:
            - Dataset
            - Entity

        Or return (pretty=False) them as a list of strings:

        ["Dataset", "Entity"]

        :param pretty: a boolean
        :return: Optional[List[str]]
        """
        return self._model.types(pretty)

    @catch
    def template(
        self, type: str, only_required: bool = False, output: str = "hjson"
    ) -> Optional[Dict]:
        """
        Print the schema associated with a given resource type (must be listed in forge.types(...)) in hjson (output='hjson') or JSON (output='json') format.
        When output='dict', a dictionary is returned.

        :param type: a resource type
        :param only_required: whether to retrieve required properties (True) or all properties (False) for a resource type
        :param output: whether to print ('hjson' or 'json') the template or return it as dictionary ('dict')
        :return: Optional[Dict]
        """
        return self._model.template(type, only_required, output)

    # No @catch because the error handling is done by execution.run().
    def validate(
        self,
        data: Union[Resource, List[Resource]],
        execute_actions_before: bool = False,
    ) -> None:
        """
        Check if resources conform to their corresponding schemas. This method will try to infer the schema of a resource from its type.
        For this method to work, a provided resource should have a type property which is listed in forge.type(...).
        It is not possible to validate a resource with a LazyAction as value of one of its property.
        The LazyAction has to be executed first (execute_actions_before=True) before validation. A report is printed after the validation is performed.

        :param data: a resource or a list of resources to validate
        :param execute_actions_before: whether to execute a LazyAction value of one of a resource property (True) or not (False) prior to validation
        :return: None
        """
        self._model.validate(data, execute_actions_before)

    # Resolving User Interface.

    def resolvers(self, output: str = "print") -> Optional[Dict]:
        """
        Print (output='print') the available resolvers or return them based as dictionary (output='dict').

        The dictionary returned has the following format:
        {
            "firstResolver": {
                "firstTarget": {
                    "bucket": "firstSource",
                },
                "secondTarget": {
                    "bucket": "secondSource",
                }
            }
        }

        :param output: defines whether the resolvers should printed or returned as a dictionary
        :return: Optional[Dict]
        """
        if output == "print":
            print("Available scopes:")
            for scope, scope_value in sorted(self._resolvers.items()):
                print(" - ", scope, ":")
                for resolver_key, resolver_value in scope_value.items():
                    print("     - resolver: ", resolver_key)
                    print(
                        "         - targets: ", ",".join(resolver_value.targets.keys())
                    )
        elif output == "dict":
            resolvers_dict = dict()
            # iterate over resolvers and fill dictionary with targets
            for scope, scope_value in sorted(self._resolvers.items()):
                individual_dict = dict()
                for resolver_key, resolver_value in scope_value.items():
                    for target_key, target_value in resolver_value.targets.items():
                        individual_dict[target_key] = {"bucket": target_value}
                resolvers_dict[scope] = individual_dict
            return resolvers_dict
        else:
            raise ValueError("unrecognized output")

    @catch
    def resolve(
        self,
        text: Union[str, List[str], Resource],
        scope: Optional[str] = None,
        resolver: Optional[str] = None,
        target: Optional[str] = None,
        type: Optional[str] = None,
        strategy: Union[ResolvingStrategy, str] = ResolvingStrategy.BEST_MATCH,
        resolving_context: Optional[Any] = None,
        property_to_resolve: Optional[str] = None,
        merge_inplace_as: Optional[str] = None,
        limit: Optional[int] = 10,
        threshold: Optional[float] = 0.5,
    ) -> Optional[Union[Resource, List[Resource], Dict[str, List[Resource]]]]:
        """
        Resolve text(s) or a resource into existing resources (from the configured Store) depending on the resolving strategy.
        Returned resources are sorted (best first) by score. See more details in the docs: https://nexus-forge.readthedocs.io/en/latest/interaction.html#resolving.

        :param text: text(s) or resources to resolve
        :param scope: a scope identifier
        :param resolver: a resolver name
        :param target: a target identifier
        :param type: a type of resources to resolve
        :param strategy:  the ResolvingStrategy to apply: BEST_MATCH (return the resource with the best score), EXACT_MATCH (return the resource with the highest score), ALL_MATCHES (return all retrieved resources sorted by score)
        :param resolving_context: A context (e.g JSON-LD context) to use during resolving
        :param property_to_resolve: the property from which the text(s) to resolve is taken when 'text' is a Resource
        :param merge_inplace_as: the property name that should hold the resolving result when 'text' is a Resource. When missing, the resolving result is returned insteada of being added to the provided resource.
        :param limit: the number of resources to retrieve
        :param threshold: the threshold score
        :return: Optional[Union[Resource, List[Resource], Dict[str, List[Resource]]]]
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
                raise AttributeError(
                    f"{scope} is not a configured resolving scope. Configured scopes are {list(self._resolvers.keys())}"
                )
            else:
                scopes_resolvers = list(self._resolvers.values())
                if resolver is not None:
                    if len(self._resolvers) == 1:
                        rov = scopes_resolvers[0][resolver]
                    else:
                        raise ResolvingError(
                            "resolving scope should be specified in case of multiple available resolvers"
                        )
                else:
                    if len(self._resolvers) == 1 and len(scopes_resolvers[0]) == 1:
                        rov = list(scopes_resolvers[0].values())[0]
                    else:
                        raise ResolvingError(
                            "resolving scope or resolver name should be "
                            "specified in case of multiple available resolvers"
                        )
            try:
                strategy = (
                    strategy
                    if isinstance(strategy, ResolvingStrategy)
                    else ResolvingStrategy[strategy]
                )
            except Exception as e:
                raise AttributeError(
                    f"Invalid ResolvingStrategy value '{strategy}'. Allowed names are {[name for name, member in ResolvingStrategy.__members__.items()]} and allowed members are {[member for name, member in ResolvingStrategy.__members__.items()]}"
                )
            return rov.resolve(
                text,
                target,
                type,
                strategy,
                resolving_context,
                property_to_resolve,
                merge_inplace_as,
                limit,
                threshold,
            )
        else:
            raise ResolvingError("no resolvers have been configured")

    # Formatting User Interface.

    @catch
    def format(self, what: str, *args) -> str:
        """
        Select a configured formatter (see https://nexus-forge.readthedocs.io/en/latest/interaction.html#formatting) string (identified by 'what') and format it using provided '*args'
        :param what: a configured formatter
        :param args: a list of string to use for formatting
        :return: str
        """
        return self._formatters[what].format(*args)

    # Mapping User Interface.

    @catch
    def sources(self, pretty: bool = True) -> Optional[List[str]]:
        """
        Print(pretty=True) or return (pretty=False) configured data sources.
        :param pretty: a boolean
        :return: Optional[List[str]]
        """
        return self._model.sources(pretty)

    @catch
    def mappings(
        self, source: str, pretty: bool = True
    ) -> Optional[Dict[str, List[str]]]:
        """
        Print(pretty=True) or return (pretty=False) configured mappings for a given source.
        Mappings are declarative rules encoding the logic of transforming data from a given source and format into resources.

        :param source: the source for which mappings are return
        :param pretty: a boolean
        :return: Optional[Dict[str, List[str]]]
        """
        return self._model.mappings(source, pretty)

    @catch
    def mapping(
        self, entity: str, source: str, type: Callable = DictionaryMapping
    ) -> Mapping:
        """
        Return a Mapping object of type 'type' for a resource type 'entity' and a source.

        :param entity: a resource type
        :param source: a data source
        :param type: a Mapping class
        :return: Mapping
        """
        return self._model.mapping(entity, source, type)

    @catch
    def map(
        self,
        data: Any,
        mapping: Union[Mapping, List[Mapping]],
        mapper: Callable = DictionaryMapper,
        na: Union[Any, List[Any]] = None,
    ) -> Union[Resource, List[Resource]]:
        """
        Transform data to resources using transformations rules provided as mappings. The format of the data to transform
        should be supported by the provided Mapper.

        :param data: data to be mapped
        :param mapping: mappings to use
        :param mapper: Mapper class to use
        :param na: represents missing values
        :return: Union[Resource, List[Resource]]
        """
        return mapper(self).map(data, mapping, na)

    # Reshaping User Interface.

    @catch
    def reshape(
        self,
        data: Union[Resource, List[Resource]],
        keep: List[str],
        versioned: bool = False,
    ) -> Union[Resource, List[Resource]]:
        """
        Keep only a provided list of properties ('keep') from a resource of list of resources.

        :param data: the resources to reshape
        :param keep: the properties to keep
        :param versioned: whether to use versioned identifier (True) or not (False)
        :return: Union[Resource, List[Resource]]
        """
        return Reshaper(self._store.versioned_id_template).reshape(
            data, keep, versioned
        )

    # Querying User Interface.

    @catch
    def retrieve(
        self,
        id: str,
        version: Optional[Union[int, str]] = None,
        cross_bucket: bool = False,
    ) -> Resource:
        """
        Retrieve a resource by its identifier from the configured store and possibly at a given version.

        :param id: the resource identifier to retrieve
        :param version: a version of the resource to retrieve
        :param cross_bucket: instructs the configured store to whether search beyond the configured bucket (True) or not (False)
        :return: Resource
        """
        return self._store.retrieve(id, version, cross_bucket)

    @catch
    def paths(self, type: str) -> PathsWrapper:
        """
        Return a PathsWrapper for a given resource type. A PathsWrapper object wraps a resource properties tree as a set of navigable paths.

        :param type: a resource type
        :return: PathsWrapper
        """
        template = self._model.template(type, False, "dict")
        return wrap_paths(template)

    @catch
    def search(self, *filters, **params) -> List[Resource]:
        """
        Search for resources based on a list of filters. The search results can be controlled (e.g. number of results) by setting parameters.
        See docs for more details: https://nexus-forge.readthedocs.io/en/latest/interaction.html#querying

        :param filters: a list of filters
        :param params: a dictionary of parameters
        :return: List[Resource]
        """
        resolvers = (
            list(self._resolvers.values()) if self._resolvers is not None else None
        )
        return self._store.search(resolvers, *filters, **params)

    @catch
    def sparql(
        self,
        query: str,
        debug: bool = False,
        limit: int = 100,
        offset: Optional[int] = None,
    ) -> List[Resource]:
        """
        Search for resources using a SPARQL query. See SPARQL docs: https://www.w3.org/TR/sparql11-query.

        :param query: a SPARQL query
        :param debug: a boolean
        :param limit: the number of resources to retrieve
        :param offset: how many results to skip from the first one
        :return: List[Resource]
        """
        return self._store.sparql(query, debug, limit, offset)

    @catch
    def elastic(
        self,
        query: str,
        debug: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Resource]:
        """
        Search for resources using an ElasticSearch DSL query. See ElasticSearch DSL docs: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html.

        :param query: an ElasticSerach DSL query
        :param debug: a boolean
        :param limit: the number of resources to retrieve
        :param offset: how many results to skip from the first one
        :return: List[Resource]
        """
        return self._store.elastic(query, debug, limit, offset)

    @catch
    def download(
        self,
        data: Union[Resource, List[Resource]],
        follow: str,
        path: str,
        overwrite: bool = False,
        cross_bucket: bool = False,
    ) -> None:
        """
        Download files attached to a resource or a list of resources.

        :param data: the resources whose attached files to download
        :param follow: the property path holding a URL to download the files
        :param path: where to output the downloaded files
        :param overwrite: whether to replace (True) and existing file with the same name or not (False)
        :param cross_bucket: instructs the configured store to whether download files beyond the configured bucket (True) or not (False)
        """
        # path: DirPath.
        self._store.download(data, follow, path, overwrite, cross_bucket)

    # Storing User Interface.

    # No @catch because the error handling is done by execution.run().
    def register(
        self, data: Union[Resource, List[Resource]], schema_id: Optional[str] = None
    ) -> None:
        """
        Store a resource or list of resources in the configured Store.

        :param data: the resources to register
        :param schema_id: an identifier of the schema the registered resources should conform to
        """
        self._store.register(data, schema_id)

    # No @catch because the error handling is done by execution.run().
    def update(
        self, data: Union[Resource, List[Resource]], schema_id: Optional[str] = None
    ) -> None:
        """
        Update a resource or a list of resources in the configured Store.

        :param data: the resources to update
        :param schema_id: an identifier of the schema the updated resources should conform to
        """
        self._store.update(data, schema_id)

    # No @catch because the error handling is done by execution.run().
    def deprecate(self, data: Union[Resource, List[Resource]]) -> None:
        """
        Deprecate a resource or a list of resources.

        :param: the resources to deprecate
        """
        self._store.deprecate(data)

    # Versioning User Interface.

    # No @catch because the error handling is done by execution.run().
    def tag(self, data: Union[Resource, List[Resource]], value: str) -> None:
        """
        Assign a tag (value) to a resource or a list of resources. A tag can be seen as a version.

        :param data: the resources to tag
        :param value: the tag value
        """
        self._store.tag(data, value)

    # No @catch because the error handling is done by execution.run().
    def freeze(self, data: Union[Resource, List[Resource]]) -> None:
        """
        Replace all resources' references within the provided resources with a versioned identifier.
        See Versioning docs: https://nexus-forge.readthedocs.io/en/latest/interaction.html#versioning.

        :param data: the resources to freeze
        """
        self._store.freeze(data)

    # Files Handling User Interface.

    @catch
    def attach(self, path: str, content_type: str = None) -> LazyAction:
        """
        Return a LazyAction for future upload  of files located in a provided path.
        The output of this method can be used to attach files to a resource: https://nexus-forge.readthedocs.io/en/latest/interaction.html#resource.

        :param path: path to upload files from
        :param content_type: the content_type of the fiels to upload
        :return: LazyAction
        """
        # path: Union[FilePath, DirPath].
        return LazyAction(self._store.upload, path, content_type)

    # Converting User Interface.

    @catch
    def as_json(
        self,
        data: Union[Resource, List[Resource]],
        expanded: bool = False,
        store_metadata: bool = False,
    ) -> Union[Dict, List[Dict]]:
        """
        Convert a resource or a list of resources to JSON.

        :param data: the resources to convert
        :param expanded: whether to expand (True) the JSON keys as URIs using a JSON-LD context (if any) or not (False)
        :param store_metadata: whether to add (True) store related metadata (e.g rev) to the output or not (False)
        :return: Union[Dict, List[Dict]]
        """
        return as_json(
            data,
            expanded,
            store_metadata,
            self._model.context(),
            self._store.metadata_context,
            self._model.resolve_context,
        )

    @catch
    @catch
    def as_jsonld(
        self,
        data: Union[Resource, List[Resource]],
        form: str = Form.COMPACTED.value,
        store_metadata: bool = False,
    ) -> Union[Dict, List[Dict]]:
        """
        Convert a resource or a list of resources to JSON-LD.

        :param data: the resources to convert
        :param form: whether to expand ('expanded') or compact ('compacted') the JSON-LD output
        :param store_metadata: whether to add (True) store related metadata (e.g rev) to the output or not (False)
        :return: Union[Dict, List[Dict]]
        """
        return as_jsonld(
            data,
            form,
            store_metadata,
            self._model.context(),
            self._store.metadata_context,
            self._model.resolve_context,
            None,
        )

    @catch
    def as_graph(
        self, data: Union[Resource, List[Resource]], store_metadata: bool = False
    ) -> Graph:
        """
        Convert a resource or a list of resources to a RDFLib Graph object: https://rdflib.readthedocs.io/en/stable/intro_to_graphs.html.

        :param data: the resources to convert
        :param store_metadata: whether to add (True) store related metadata (e.g rev) to the output or not (False)
        :return: rdflib.Graph
        """
        return as_graph(
            data,
            store_metadata,
            self._model.context(),
            self._store.metadata_context,
            self._model.resolve_context,
        )

    @catch
    def as_dataframe(
        self,
        data: Union[Resource, List[Resource]],
        na: Union[Any, List[Any]] = [None],
        nesting: str = ".",
        expanded: bool = False,
        store_metadata: bool = False,
    ) -> DataFrame:
        """
        Convert a resource or a list of resources to pandas.DataFrame.

        :param data: the resources to convert
        :param na: represents missing values
        :param nesting: str to use to join when flattening nested properties as columns
        :param expanded: whether to expand (True) resources' properties as URIs using a JSON-LD context (if any) or not (False)
        :param store_metadata: whether to add (True) store related metadata (e.g rev) to the output or not (False)
        :return: pandas.DataFrame
        """
        return as_dataframe(
            data,
            na,
            nesting,
            expanded,
            store_metadata,
            self._model.context(),
            self._store.metadata_context,
            self._model.resolve_context,
        )

    @catch
    def from_json(
        self, data: Union[Dict, List[Dict]], na: Union[Any, List[Any]] = None
    ) -> Union[Resource, List[Resource]]:
        """
        Convert a JSON document or a list of JSON documents to a resource or a list of resources.

        :param data: the JSON documents to convert
        :param na: represents missing values
        :return: Union[Resource, List[Resource]]
        """
        return from_json(data, na)

    @catch
    def from_jsonld(
        self, data: Union[Dict, List[Dict]]
    ) -> Union[Resource, List[Resource]]:
        """
        Convert a JSON-LD document or a list of JSON-LD documents to a resource or a list of resources.

        :param data: the JSON-LD documents to convert
        :return: Union[Resource, List[Resource]]
        """
        return from_jsonld(data)

    @catch
    def from_graph(
        self,
        data: Graph,
        type: Union[str, List[str]] = None,
        frame: Dict = None,
        use_model_context=False,
    ) -> Union[Resource, List[Resource]]:
        """
        Convert a RDFLib.Graph object to a resource or a list of resources. What to convert from the RDFLib.Graph can be
        selected by type and how to shape them as resources can be controlled using a JSON-LD Frame: https://www.w3.org/TR/json-ld11-framing.

        :param data: the RDFLib.Graph object to convert
        :param type: the types of RDF resources to convert from the RDFLib.Graph object
        :param frame: the JSON-LD frame to apply during conversion
        :param use_model_context: whether to use  (True) the JSON-LD context from the configured Model or not (False)
        :return: Union[Resource, List[Resource]]
        """
        context = self._model.context() if use_model_context else None
        return from_graph(data, type, frame, context)

    @catch
    def from_dataframe(
        self, data: DataFrame, na: Union[Any, List[Any]] = np.nan, nesting: str = "."
    ) -> Union[Resource, List[Resource]]:
        """
        Convert a pandas.DataFrame to a resource or a list of resources.

        :param data: the pandas.DataFrame to convert
        :param na: represents missing values
        :param nesting: str to use to detect nested nested properties
        :return: Union[Resource, List[Resource]]
        """
        return from_dataframe(data, na, nesting)


def prepare_resolvers(
    config: Dict, store_config: Dict
) -> Dict[str, Dict[str, Resolver]]:
    return {
        scope: dict(prepare_resolver(x, store_config) for x in configs)
        for scope, configs in config.items()
    }


def prepare_resolver(config: Dict, store_config: Dict) -> Tuple[str, Resolver]:
    if config["origin"] == "store":
        with_defaults(
            config,
            store_config,
            "source",
            "name",
            [
                "endpoint",
                "token",
                "bucket",
                "model_context",
                "searchendpoints",
                "vocabulary",
            ],
        )
    resolver_name = config.pop("resolver")
    resolver = import_class(resolver_name, "resolvers")
    return resolver.__name__, resolver(**config)
