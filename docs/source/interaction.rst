Knowledge graph interaction
===========================

Forge
-----

With Nexus Forge, creating knowledge graphs from data sources potentially using data transformations and registering
them in a Store or searching data from it, starts by initialising a `KnowledgeGraphForge` session:

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   forge = KnowledgeGraphForge(configuration: Union[str, Dict], **kwargs)

where the `configuration` accepts:

* an YAML formatted content inline, from a file path or from a URL,
* or a JSON format content inline

The required minimal configuration defines:

* a `Store` for storing, managing and accessing knowledge graphs.
  By default, Nexus Forge comes with the support of an in memory `DemoStore` and a persistent `BlueBrainNexus` store based
  on `Blue Brain Nexus Delta <https://bluebrainnexus.io/products/nexus-delta>`__. Other stores can be added by implementing Nexus
  Forge's `kgforge.core.archetypes.store.Store` interface.

* a Model implementing a schema language to validate and constraint knowledge graphs. By default, Nexus Forge comes
  with a `DemoModel` supporting the JSON format and a `RdfModel` supporting the
  `W3C Shapes Constraint Language (SHACL) <https://www.w3.org/TR/shacl>`__. Other schemas languages
  can be added by implementing Nexus Forge's `kgforge.core.archetypes.model.Model` interface.

.. code-block:: yaml

    Model:
      name: <a class name of a Model implementing a data schema language>
      origin: < allowed values are 'directory', 'web_service', or 'store'>
      source: <a directory path, a URL, or the class name of a Store from which schemas can be loaded>
    Store:
      name: <the class name of the Store to use>

A minimal YAML formatted configuration for each of Demo BlueBrainNexus stores would look like:

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   config_DemoStore = """
       Model:
          name: DemoModel
          origin: directory
          source: ../../../tests/data/demo-model/
       Store:
          name: DemoStore
    """

   config_BlueBrainNexus = """
       Model:
          name: RdfModel
          origin: store         # 'directory' can be provided in case schemas are stored in a folder
          bucket: <org/project> # A Blue Brain Nexus organisation and project can be provided as bucket
       Store:
          name: BlueBrainNexus,
          "endpoint":"https://bluebrainnexus_deployment_address"
          bucket: <org/project> # A Blue Brain Nexus organisation and project can be provided as bucket

    """
   forge = KnowledgeGraphForge(configuration=config)

See the `configuration documentation page section <https://nexus-forge.readthedocs.io/en/latest/configuration.html>`__ for a full list of forge configuration and see the `examples/notebooks/use-cases/` folder
for more real world YAML examples.

Resource
--------

Try |Binder|

A *Resource* is the base data exchange object in Nexus Forge. It is an identifiable data object with potentially a set of properties as metadata.
Reserved properties of a `Resource` are: `id`, `type` and `context`.

A Resource can be created using:

* keyword arguments:

.. code-block:: python

   from kgforge.core import Resource
   resource = Resource(name="Jane Doe", type="Person", email="jane.doe@example.org")

* a JSON dictionary:

.. code-block:: python

   from kgforge.core import Resource
   data = {
    "name": "Jane Dow",
    "type" : "Person",
    "email" : "jane.doe@example.org"
   }
   resource = Resource(data)

* or a dataframe:

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   import pandas as pd
   forge = KnowledgeGraphForge(configuration= "./config.yml", **kwargs)
   dataframe = pd.read_csv("data.csv")
   resources = forge.from_dataframe(dataframe)

A resource can have files attached by assigning the output of `forge.attach` method to a property in the resource:

.. code-block:: python

   resource.picture = forge.attach("path/to/file.jpg")

Dataset
-------

A Dataset is a specialization of a `Resource` that provides users with operations to handle files,
record their provenance and describe them with metadata. The metadata of `Datasets` refers specifically to, but not limited to:

* Provenance:

  * contribution (people, organizations or software agents that contributed to the creation of the Dataset),
  * `generation <https://www.w3.org/TR/prov-o/#Generation>`__ (links to resources used to generate this Dataset),
  * `derivation <https://www.w3.org/TR/prov-o/#Derivation>`__ (links another resource from which the Dataset is generated),
  * `invalidation <https://www.w3.org/TR/prov-o/#Invalidation>`__ (data became invalid)

* Data storage and access:
  * `distribution <https://schema.org/distribution>`__ (a downloadable form of the Dataset, at a specific location, in a specific format)

The `Dataset` class provides methods for adding files to a `Dataset`. The added files will only be uploaded in the Store when the `forge.register` function is
called on the Dataset so that the user flow is not slowed down and for efficiency purpose. This is done using
the concept of `LazyAction`, which is a class that will hold an action that will be executed when required.

After the registration of the Dataset, a `DataDownload <https://schema.org/DataDownload>`__ resource will be added with automatically
extracted properties, such as the file content type, size, name, etc.

The `Dataset` signature class corresponds to:

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

Creating a `Dataset` object can be done with:

.. code-block:: python

    from kgforge.core import KnowledgeGraphForge
    from kgforge.specializations.resources import Dataset
    forge = KnowledgeGraphForge(configuration= "./config.yml", **kwargs)
    dataset = Dataset(forge, name="Interesting dataset")
    dataset.add_distribution("path/to/file.jpg", content_type="image/jpeg")

Storing
-------

Storing allows users to persist and manage `Resources` in the configured store. Resources contain additional
hidden properties accounting for their state and allowing recovering from errors:

* `_last_action`, contains information about the last action that took place in the resource (e.g. register, update, etc.)
* `_synchronized`, indicates that the last action succeeded
* `_store_metadata`, keeps additional resource metadata potentially provided by the store such as version, creation date, etc.

The `Store` interface exposes the following functions related to storing resources:

.. code-block:: python

   forge.register(data: Union[Resource, List[Resource]], schema_id: Optional[str]=None) -> None
   forge.update(data: Union[Resource, List[Resource]]) -> None
   forge.deprecate(data: Union[Resource, List[Resource]]) -> None

Storing a `Dataset` (or a `Resource`) can be performed as follows:

.. code-block:: python

    from kgforge.core import KnowledgeGraphForge
    from kgforge.specializations.resources import Dataset

    forge = KnowledgeGraphForge(configuration= "./config.yml", **kwargs)
    dataset = Dataset(forge, name="Interesting dataset")
    dataset.add_distribution("path/to/file.jpg", content_type="image/jpeg")
    forge.register(dataset)

Querying
--------

Stored resources can be searched from a store (1) by id, (2) by specifying filters in key<op>value or dict format, (3) by using
SPARQL query if supported by the store (4) or by using an ElasticSearch query if supported by the store.

.. code-block:: python

   forge.retrieve(id: str, version: Optional[Union[int, str]] = None, cross_bucket: bool = False) -> Resource
   forge.paths(type: str) -> PathsWrapper # introspect a schema by type and return all defined property paths
   forge.search(*filters, **params) -> List[Resource] # a cross_bucket param can be used to enable cross bucket search (True) or not (False)
   forge.sparql(query: str, debug: bool, limit: int, offset: int = None) -> List[Resource]
   forge.elastic(query: str, debug: bool, limit: int, offset: int = None) -> List[Resource] # for elasticsearch query
   forge.download(data: Union[Resource, List[Resource]], follow: str, path: str, overwrite: bool = False) -> None

Currently `forge.search(*filters, **params)` will rewrite the filters as SPARQL query undre the hood.
When the `cross_bucket=True` param is set, then it can be complemented with a 'bucket=<str>' param to filter the bucket to search in.

Next are examples of search calls:

.. code-block:: python

    from kgforge.core import KnowledgeGraphForge
    from kgforge.specializations.resources import Dataset
    forge = KnowledgeGraphForge(configuration="./config.yml", **kwargs)

    # Retrieve by id at a given version
    result = forge.retrieve(id="...", version="version")
    # Filter by type using a dictionary
    filters = {"type":"Dataset"}
    results_filters = forge.search(filters, limit=10, offset=0, deprecated=False)
    # Filter by type using a paths
    paths = forge.paths("Dataset")
    result_paths = forge.search(paths.type=="Dataset", limit=10, offset=0, deprecated=False)

Versioning
----------

Resources can be versioned, if the configured `Store` supports it. `forge.tag` is equivalent to a git tag while
`forge.freeze` replaces all resources' references within a given `Resource` by a version identifier

The `KnowledgeGraphForge` class exposes the following functions related to versioning resources:

.. code-block:: python

   forge.tag(data: Union[Resource, List[Resource]], value: str) -> None
   forge.freeze(data: Union[Resource, List[Resource]]) -> None

Next are examples of resource tag and freeze calls:

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   from kgforge.specializations.resources import Dataset

   forge = KnowledgeGraphForge(configuration="./config.yml")
   dataset = Dataset(forge, name="Interesting dataset")
   dataset.add_distribution("path/to/file.jpg", content_type="image/jpeg")
   forge.register(dataset)
   forge.tag(data=dataset, value="v1.0.0) # Any str can be used for 'value'
   forge.freeze(data=dataset)

Converting
----------

To use `Resources` with other libraries such as `pandas <https://pandas.pydata.org/>`__ and `RDFLib <https://rdflib.readthedocs.io/en/stable/>`__,
different conversion functions are available.

.. code-block:: python

   forge.as_json(data: Union[Resource, List[Resource]], expanded: bool = False, store_metadata: bool = False) -> Union[Dict, List[Dict]]
   forge.as_jsonld(data: Union[Resource, List[Resource]], compacted: bool = True, store_metadata: bool = False) -> Union[Dict, List[Dict]]
   forge.as_graph(data: Union[Resource, List[Resource]], store_metadata: bool = False) -> Graph
   forge.as_dataframe(data: Union[Resource, List[Resource]], na: Union[Any, List[Any]] = [None], nesting: str = ".", expanded: bool = False, store_metadata: bool = False) -> DataFrame
   forge.from_json(data: Union[Dict, List[Dict]], na: Union[Any, List[Any]] = None) -> Union[Resource, List[Resource]]
   forge.from_jsonld(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]
   forge.from_graph(data: rdflib.Graph, type = Optional[Union[str, List]] = None, frame: Dict = None, model_context: Optional[Context] = None) -> Union[Resource, List[Resource]]
   forge.from_dataframe(data: DataFrame, na: Union[Any, List[Any]] = np.nan, nesting: str = ".") -> Union[Resource, List[Resource]]

For example resources can be created from a pandas dataframe:

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   import pandas as pd
   forge = KnowledgeGraphForge(configuration= "./config.yml")
   dataframe = pd.read_csv("data.csv")
   resources = forge.from_dataframe(dataframe)

Formatting
----------

A preconfigured set of string formats can be provided to ensure the consistency of data.

.. code-block:: python

   forge.format(what: str, *args) -> str

Next is an example of formatting a resource identifier with a namespace. This make all resources identifiers
fall under the same namespace.

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   from kgforge.core import Resource
   config = """
               Model:
                  name: DemoModel
                  origin: directory
                  source: ../../../tests/data/demo-model/
               Store:
                  name: DemoStore
               Formatters:
                  identifier: https://example.org/{}
            """
   forge = KnowledgeGraphForge(configuration= config)
   _id = forge.format(what="identifier", "uuid")
   resource = Resource(id=_id, name="Jane Doe", type="Person")

Resolving
---------

A `Resolver` is used to link terms or a `Resource` to identifiers (URIs) in a knowledge graph thus addressing lexical variations
(merging of synonyms, aliases and acronyms) and disambiguating them. This feature is also referred to as entity linking
specially in the context of Natural Language Processing (NLP) when building knowledge graph from entities extracted from
text documents. For example the text `USA` and `America` can be both resolved (or link) to the same DBpedia URI
`http://dbpedia.org/resource/United_States` using the `DBpedia look up service <https://lookup.dbpedia.org/>`__.

`Resolving` involves two main steps:
 * **candidates generation**: resolving often results in many possible resources to link to called candidates.
   Each candidate is associated with a score representing how close it is to the input text to resolve.
   Candidates then can be ranked based on different criteria (e.g score, context of occurence in a given document)
   combined using different strategies including exact or fuzzy matches. For example resolving the text Amereica
   using the `DBpedia look up service <https://lookup.dbpedia.org/>`__ yields the following 2 first candidates:
   `http://dbpedia.org/resource/United_States` and `http://dbpedia.org/resource/California`. There is a decision to be
   made about which candidate represents the best the text `America` within a given context.
   In Nexus Forge, resolving candidates are `Resources` of type
   `kgforge.core.specializations.resources.entity_linking_candidate.EntityLinkingCandidate`.

* **candidates ranking**: currently, supported candidates ranking criteria is their scores. The following strategies
  are available:

  * `kgforge.core.commons.strategies.ResolvingStrategy.EXACT_MATCH`: Only candidates with a perfect score
    (usually 0 for a distance based score or 1 for a normalised similarity score) are considered and one of them is picked.

  * `kgforge.core.commons.strategies.ResolvingStrategy.BEST_MATCH` (default): Only candidates with the highest scores
    that are potentially below a threshold (default to 0.5) are considered is one them is picked.

  * `kgforge.core.commons.strategies.ResolvingStrategy.ALL_MATCHES`: A list of candidates with scores potentially below a
    threshold are considered. The size of the list of candidates can be controlled with a parameter (default to 10).

The `KnowledgeGraphForge` class exposes the following function for resolving a str, list of str or a `Resource`:

.. code-block:: python

   forge.resolve(text: Union[str, List[str], Resource], scope: Optional[str] = None, resolver: Optional[str] = None,
                target: Optional[str] = None, type: Optional[str] = None,
                strategy: Union[ResolvingStrategy, str] = ResolvingStrategy.BEST_MATCH,
                resolving_context: Optional[Any] = None, property_to_resolve: Optional[str] = None,
                merge_inplace_as: Optional[str] = None, limit: Optional[int] = 10, threshold: Optional[float] = 0.5
                ) -> Optional[Union[Resource, List[Resource], Dict[str, List[Resource]]]]


The following code shows the configuration of a `scikit-learn <https://scikit-learn.org/stable/>`__ based `Resolver`
using the class `kgentitylinkingsklearn.EntityLinkerSkLearn` and loading a model file named
`tfidfvectorizer_model_schemaorg_linking` (bucket) from a directory (source). The model in this example is a very simple
`TfidfVectorizer <https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html>`__
trained on `schema.org <https://schema.org/>`__ classes. The resulting resource will be mapped to
the json structure defined in the `result_resource_mapping` file.

Full resolver config options and real world examples

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   from kgforge.core import Resource
   from kgforge.core.commons.strategies import ResolvingStrategy
   # perform pip install nexusforge[linking_sklearn] to use the scikit-learn based resolver
   config = """
               Model:
                  name: DemoModel
                  origin: directory
                  source: ../../../tests/data/demo-model/
               Store:
                  name: DemoStore
               Resolvers:
                  schemaorg:
                    - resolver: EntityLinkerSkLearn from kgentitylinkingsklearn
                      origin: directory
                      source: "../../data/"
                      targets:
                        - identifier: terms
                          bucket: tfidfvectorizer_model_schemaorg_linking
                      result_resource_mapping: ../../configurations/entitylinking-resolver/entitylinking-mapper.hjson

            """
   forge = KnowledgeGraphForge(configuration= config)
   forge.resolve(text="person", scope="schemaorg", target="terms", strategy=ResolvingStrategy.BEST_MATCH)
   resource = Resource(id=_id, name="Jane Doe", type="Person")


A `scope` is a convenient (and arbitrary) way to name a given `Resolver` along with a set of sources of data
(the `targets`) to resolve against.

Nexus Forge comes with the support of 5 types Resolvers:

* **OntologyResolver**: based on type, label and notation (ie. acronym) filtering using a SPARQL query to generate candidates.
  An example of configuration is available at `examples/notebooks/use-cases/prod-forge-nexus.yml`.

* **EntityLinkerSkLearn**: based on a pretrained model and using `scikit-learn <https://scikit-learn.org/stable/>`__.
  to generate and rank candidates. To customise the configuration of this resolver
  (as shown in the resolving example above):

  * Nexus Forge should be installed as follows `pip install nexusforge[linking_sklearn]`

  * `resolver` value should be set to `EntityLinkerSkLearn from kgentitylinkingsklearn`

  * `origin` value should be set to 'directory'

  * a folder containing the model should be provided as `source` value

  * a file name should be provided as value `bucket` under `targets`

  * a `result_resource_mapping` file should be provided to map the result to a json structure

  An example of configuration for `EntityLinkerSkLearn` is available at
  `examples/notebooks/use-cases/EntityLinkerSkLearn-forge-demo-config.yml`.

* **EntityLinkerElastic**: based on `ElasticSearch text similarity search <https://www.elastic.co/blog/text-similarity-search-with-vectors-in-elasticsearch>`__
  to generate and rank candidates but require a text embedding or encoding service to compute embeddings of items.
  An example of configuration is available at `examples/notebooks/use-cases/EntityLinkerElastic-forge-demo-config.yml`. .

* **AgentResolver**: based on type, full, given or family names filtering using a SPARQL query to generate candidates.
  An example of configuration is available at `examples/notebooks/use-cases/prod-forge-nexus.yml`.

* **DemoResolver**: an example resolver based on filtering by configurable properties and looking up candidates from a json file.
  An example of configuration is available at `examples/notebooks/use-cases/EntityLinkerSkLearn-forge-demo-config.yml`.

Reshaping
---------

Reshaping allows keeping only a specific set of properties of a resource.

.. code-block:: python

   forge.reshape(data: Union[Resource, List[Resource]], keep: List[str], versioned: bool = False) -> Union[Resource, List[Resource]]

Next is an example of reshaping a resource.

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   from kgforge.core import Resource
   forge = KnowledgeGraphForge(configuration= "./config.yml")
   resource = Resource(id=_id, name="Jane Doe", type="Person", email="jane.doe@example.org")
   forge.reshape(data=resource, keep=["id","name"]) # type and email will be removed

Modeling
--------

The `KnowledgeGraphForge` class exposes a set of methods to access configured data types (`forge.types`) along with
their schemas (`forge.template`) in the form a JSON dictionary. `forge.validate` validates resources against their
corresponding schemas inferred from their types.
In case a `kgforge.specializations.models.rdf_model.RdfModel` is configured, `forge.prefixes` returns the
`JSON-LD <https://json-ld.org/>`__ prefix mappings.
The schema templates can be used to create empty resources objects to populate with actual data.

.. code-block:: python

   forge.types(pretty: bool = True) -> Optional[List[str]]
   forge.template(type: str, only_required: bool = False) -> None
   forge.validate(data: Union[Resource, List[Resource]], execute_actions_before: bool = False) -> None
   forge.prefixes(pretty: bool = True) -> Optional[Dict[str, str]]

The next example shows how to create and valdiate a resource from a template representing a schema.

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   from kgforge.core import Resource
   forge = KnowledgeGraphForge(configuration= "./config.yml")

   print(forge.types()) # Output can be: Person
   template = forge.template("Person", output="dict", only_required=True) # Output can be {"type":"Person", "name":""}
   template["name"] = "Jane"
   resource = forge.from_json(template)
   forge.validate(resource)

Mapping
-------

Mappings are declarative rules encoding the logic of transforming data from a given source and format into resources.
The transformations rules are parsed by a `kgforge.core.archetypes.mapping.Mapping` and are executed by a
`kgforge.core.archetypes.mapper.Mapper`. By default, Nexus Forge comes with a `kgforge.specializations.mappings.dictionaries.DictionaryMapping`
and a `kgforge.specializations.mappers.dictionaries.DictionaryMapper` accepting JSON formatted transformations rules.

The `KnowledgeGraphForge` class exposes the following method to map data to ressources.

.. code-block:: python

 forge.map(data: Any, mapping: Union[Mapping, List[Mapping]], mapper: Callable = DictionaryMapper, na: Union[Any, List[Any]] = None) -> Union[Resource, List[Resource]]

Next is an example of mapping a JSON formatted data into a different JSON shape with values formatted (id),
concatenated (name), resolved (gender) to link them to ontology terms for example or checked for presence (additionalName).

.. code-block:: python

   from kgforge.core import KnowledgeGraphForge
   forge = KnowledgeGraphForge(configuration= "./config.yml")
   data= {
        "id": 123,
        "givenName": "Marie",
        "familyName": "Curie",
        "gender": "female"
    }
   mapping_rules = DictionaryMapping("""
    type: Contribution
    agent:
    {
        id:  forge.format("identifier", x.id)
        type: Person
        givenName: x.givenName,
        familyName: x.familyName,
        name: f"{x.givenName}/{x.familyName}"
        gender: forge.resolve(text=x.gender, scope="ontologies", target="terms")
        additionalName: x.middle_name if middle_name in x else ''
    }""")
   resource = forge.map(data=data, mapping=mapping_rules, na='') # by default the DictionaryMapper is used

.. |Binder| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.6.0?filepath=examples%2Fnotebooks%2Fgetting-started
