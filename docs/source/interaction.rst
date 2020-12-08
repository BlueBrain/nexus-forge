Knowledge graph interaction
===========================

Forge
-----

Forge initialization signature is:

.. code-block:: python

   KnowledgeGraphForge(configuration: Union[str, Dict], **kwargs)

where the `configuration` accepts a YAML file or a JSON dictionary, and `**kwargs` can
be used to override the configuration provided for the Store.

The YAML configuration has the following structure:

.. code-block:: yaml

   Model:
     name: <a class name of a Model>
     origin: <'directory', 'url', or 'store'>
     source: <a directory path, an URL, or the class name of a Store>
     bucket: <when 'origin' is 'store', a Store bucket, a section or segment in the Store>
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

and the python configuration would be like:

.. code-block:: python

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

The required minimal configuration is:

* `name` for Model and Store
* `origin` and `source` for Model

See `nexus-forge/examples/configurations/` for YAML examples.

Create a forge instance:

.. code-block:: python

   forge = KnowledgeGraphForge("../path/to/configuration.yml")

Resource
--------

A *Resource* is an identifiable data object with a set of properties. It is mainly identified by its *Type*,
which value is a concept, such as, Person, Contributor, Organisation, Experiment, etc. Reserved properties of a
Resource are: `id`, `type` and `context`.

Create a resource using keyword arguments, a JSON dictionary, or a dataframe:

.. code-block:: python

   resource = Resource(name="Jane Doe", type="Person", email="jane.doe@examole.org")

.. code-block:: python

   data = {
    "name": "Jane Dow",
    "type" : "Person",
    "email" : "jane.doe@examole.org"
   }
   resource = Resource(data)

.. code-block:: python

   import pandas as pd

   dataframe = pd.read_csv("data.csv")

   resources = forge.from_dataframe(dataframe)

A resource can have files attached by assigning the output of `forge.attach` method to a property in the resource:

.. code-block:: python

   resource.picture = forge.attach("path/to/file.jpg")

Dataset
-------

A Dataset is a specialization of a `Resource` that provides users with operations to handle files
and describe them with metadata. The metadata of `Datasets` refers specifically to, but not limited to:

* provenance:

  * contribution (people, organizations or software agents that contributed to the creation of the Dataset),
  * `generation <https://www.w3.org/TR/prov-o/#Generation>`__ (links to resources used to generate this Dataset),
  * `derivation <https://www.w3.org/TR/prov-o/#Derivation>`__ (links another resource from which the Dataset is generated),
  * `invalidation <https://www.w3.org/TR/prov-o/#Invalidation>`__ (data became invalid)

* access: `distribution <https://schema.org/distribution>`__ (a downloadable form of this Dataset, at a specific location, in a specific format)

The `Dataset` class provides methods for adding files to a `Dataset`. The added files will only be uploaded in the Store when the `forge.register` function is
called on the Dataset so that the user flow is not slowed down and for efficiency purpose. This is done using
the concept of `LazyAction`, which is a class that will hold an action that will be executed when required.

After the registration of the Dataset, a `DataDownload` resource will be created with automatically
extracted properties, such as content type, size, file name, etc.

.. code-block:: python

   Dataset(forge: KnowledgeGraphForge, type: str = "Dataset", **properties)
     add_parts(resources: List[Resource], versioned: bool = True) -> None
     add_distribution(path: str, content_type: str = None) -> None
     add_contribution(resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None
     add_generation(resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None
     add_derivation(resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None
     add_invalidation(resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None
     add_files(path: str, content_type: str = None) -> None
     download(path: str, source: str, overwrite: bool = False) -> None

Storing
-------

Storing allows us to persist and manage Resources in the configured Store. Resources contain additional
information in hidden properties to allow users recovering from errors:

* `_synchronized`, indicates that the last action succeeded
* `_last_action`, contains information about the last action that took place in the resource (e.g. register, update, etc.)
* `_store_metadata`, keeps additional resource metadata provided by the store such as version, creation date, etc.

.. code-block:: python

   register(data: Union[Resource, List[Resource]]) -> None
   update(data: Union[Resource, List[Resource]]) -> None
   deprecate(data: Union[Resource, List[Resource]]) -> None

Querying
--------

It is possible to retrieve resources from the store by (1) its id, (2) specifying filters with
the properties and a specific value and (3) using a simplified version of SPARQL query.

.. code-block:: python

   retrieve(id: str, version: Optional[Union[int, str]] = None, cross_bucket: bool = False) -> Resource
   paths(type: str) -> PathsWrapper
   search(*filters, **params) -> List[Resource] # a cross_bucket param can be used to enable cross buket search (True) or not (False)
   sparql(query: str) -> List[Resource]
   download(data: Union[Resource, List[Resource]], follow: str, path: str, overwrite: bool = False) -> None

When the 'cross_bucket=True' param is used in forge.search, then it can be complemented with a 'bucket=<str>' param to
filter the bucket to search in.

Versioning
----------

The user can create versions of Resources, if the Store supports this feature.

.. code-block:: python

   tag(data: Union[Resource, List[Resource]], value: str) -> None
   freeze(data: Union[Resource, List[Resource]]) -> None

Converting
----------

To use Resources with other libraries such as pandas, different data conversion functions are available.

.. code-block:: python

   as_json(data: Union[Resource, List[Resource]], expanded: bool = False, store_metadata: bool = False) -> Union[Dict, List[Dict]]
   as_jsonld(data: Union[Resource, List[Resource]], compacted: bool = True, store_metadata: bool = False) -> Union[Dict, List[Dict]]
   as_graph(data: Union[Resource, List[Resource]], store_metadata: bool = False) -> Graph
   as_dataframe(data: List[Resource], na: Union[Any, List[Any]] = [None], nesting: str = ".", expanded: bool = False, store_metadata: bool = False) -> DataFrame
   from_json(data: Union[Dict, List[Dict]], na: Union[Any, List[Any]] = None) -> Union[Resource, List[Resource]]
   from_jsonld(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]
   from_graph(data: rdflib.Graph, type = Optional[Union[str, List]] = None, frame: Dict = None, model_context: Optional[Context] = None) -> Union[Resource, List[Resource]]
   from_dataframe(data: DataFrame, na: Union[Any, List[Any]] = np.nan, nesting: str = ".") -> Union[Resource, List[Resource]]

Formatting
----------

A preconfigured set of string formats can be provided to ensure the consistency of data.

.. code-block:: python

   format(what: str, *args) -> str

Resolving
---------

Resolvers are helpers to find commonly used resources that one may want to link to. For instance, one could have a set of pre-defined identifiers of Authors, and to make several references to the same Authors, a resolver can be used.

.. code-block:: python

   resolve(text: str, scope: Optional[str] = None, resolver: Optional[str] = None, target: Optional[str] = None, type: Optional[str] = None, strategy: ResolvingStrategy = ResolvingStrategy.BEST_MATCH) -> Optional[Union[Resource, List[Resource]]]

Reshaping
---------

Reshaping allows trimming Resources by a specific set of properties.

.. code-block:: python

   reshape(data: Union[Resource, List[Resource]], keep: List[str], versioned: bool = False) -> Union[Resource, List[Resource]]

Modeling
--------

To create *Resources*, the user can make use of Modeling functions. The user can explore
predefined *Types* and the properties that describe them via *Templates*. *Templates* can be used
to create resources with the specified properties. Resources that
are created using a template can be validated.

.. code-block:: python

   context() -> Optional[Dict]
   prefixes(pretty: bool = True) -> Optional[Dict[str, str]]
   types(pretty: bool = True) -> Optional[List[str]]
   template(type: str, only_required: bool = False) -> None
   validate(data: Union[Resource, List[Resource]]) -> None

Mapping
-------

Mappings are pre-defined configuration files that encode the logic on how to transform a specific
data source into Resources that follow a template of a targeted *Type*.
For instance, when different versions of the same dataset is regularly integrated, one can make
use of Mappers to specify how the coming data is going to be integrated using the corresponding
typed *Resource*.

.. code-block:: python

   sources(pretty: bool = True) -> Optional[List[str]]
   mappings(source: str, pretty: bool = True) -> Optional[Dict[str, List[str]]]
   mapping(entity: str, source: str, type: Callable = DictionaryMapping) -> Mapping
   map(data: Any, mapping: Union[Mapping, List[Mapping]], mapper: Callable = DictionaryMapper, na: Union[Any, List[Any]] = None) -> Union[Resource, List[Resource]]
