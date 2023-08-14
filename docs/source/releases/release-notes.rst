=============
Release Notes
=============

This release introduces new features and enhancements to Nexus Forge while fixing a couple of bugs.

New Features
============

Resolving
---------

|Binder_Resolving| and |Binder_Resolving_UseCase| to try.


* It is now possible to configure a property path filter for a SPARQL based Resolver (`OntologyResolver` and `AgentResolver`) target to better narrow down data to resolve to within a given bucket `#290 <https://github.com/BlueBrain/nexus-forge/pull/290>`__, `#312 <https://github.com/BlueBrain/nexus-forge/pull/312>`__ .
  This allows for example a user to target a specific ontology to resolve a string from. Here is the complete configuration of a Resolver:
 
 .. code-block:: python

   Resolvers:
     <scope>:
       - resolver: <a class name of a Resolver>
         origin: <'directory', 'web_service', or 'store'>
         source: <a directory path, a web service endpoint, or the class name of a Store>
         targets:
           - identifier: <a name, or an IRI>
             bucket: <a file name, an URL path, or a Store bucket>
             filters:
               - path: <a resource property path>
               - value: <a resource property value to filter with>
         searchendpoints:
          sparql:
            endpoint: <A SPARQL endpoint to send resolving query to. Only used for resolvers based on SPARQL>
         result_resource_mapping: <an Hjson string, a file path, or an URL>
         endpoint: <when 'origin' is 'store', a Store endpoint, default to Store:endpoint>
         token: <when 'origin' is 'store', a Store token, default to the token provided in the configured Store>

An example of configuration for an OntologyResolver is:

.. code-block:: python

   config = """
               Resolvers:
                  ontology:
                    - resolver: OntologyResolver
                      origin: store
                      source: BlueBrainNexus
                      targets:
                        - identifier: terms
                        bucket: neurosciencegraph/datamodels
                        - identifier: CellType
                        bucket: neurosciencegraph/datamodels
                        filters:
                            - path: subClassOf*.id
                            value: BrainCellType
                        - identifier: BrainRegion
                        bucket: neurosciencegraph/datamodels
                        filters:
                            - path: subClassOf*.id
                            value: BrainRegion
                        - identifier: Species
                        bucket: neurosciencegraph/datamodels
                        filters:
                            - path: subClassOf*.id
                            value: Species
                      searchendpoints:
                        sparql:
                          endpoint: "https://bluebrain.github.io/nexus/vocabulary/defaultSparqlIndex"
                      result_resource_mapping: https://raw.githubusercontent.com/BlueBrain/nexus-forge/master/examples/configurations/nexus-resolver/term-to-resource-mapping.hjson

            """
   forge.resolve(text="Chapter", scope="schemaorg_CreativeWork", target="CreativeWork", strategy=ResolvingStrategy.EXACT_MATCH)

A specific configured target can be specified as usual when resolving:

.. code-block:: python

    # forge.resolvers() lists configured resolvers 
    forge.resolve(text="MC", scope="ontology", target="CellType", strategy=ResolvingStrategy.EXACT_MATCH)


Enhancements
============

Resource
--------

|Binder_Resource| to try the enhancements.

* Added methods to get a Resource identifier (`Resource.has_identifier()` will look for `id` and `@id`) or type (`Resource.has_type()` will lok for `type` or `@type`) `#265 <https://github.com/BlueBrain/nexus-forge/pull/265>`__ , `#318 <https://github.com/BlueBrain/nexus-forge/pull/318>`__.


Querying
--------

|Binder_Querying| to try the enhancements.

* Added more SPARQL clauses (such as `optional`, `as` or `describe`) to ignore when rewriting (using `Store.rewrite_sparql()`) a SPARQL query `#288 <https://github.com/BlueBrain/nexus-forge/pull/288>`__, `#292 <https://github.com/BlueBrain/nexus-forge/pull/292>`__, `#297 <https://github.com/BlueBrain/nexus-forge/pull/297>`__.
* Added support for specifying a content-type when downloading data `#265 <https://github.com/BlueBrain/nexus-forge/pull/265>`__ (issue `#251 <https://github.com/BlueBrain/nexus-forge/pull/251>`__).
* Updated SPARQL query statement builder to consider the values of resource properties `@id` and `@type` as URIs (so that the values get correctly rewritten as follows: `<uri>`) when used with the `NOT_EQUAL` search operator `#265 <https://github.com/BlueBrain/nexus-forge/pull/265>`__.
* Introduced `core/commons/sparql_query_builder.SPARQLQueryBuilder` for building SPARQL select query statements and filters `#290 <https://github.com/BlueBrain/nexus-forge/pull/290>`__.
* `BlueBrainNexus` store: added resource retrieval by _self value (`Resource._store_metadata._self`) in addition to `Resource.id` `#271 <https://github.com/BlueBrain/nexus-forge/pull/271>`__.
* Added support for chaining multiple json properties using `/` as keys when calling searching using the filter dict syntax `#305 <https://github.com/BlueBrain/nexus-forge/pull/305>`__.

.. code-block:: python

    # Filter by type using a dictionary. affiliation and id are chained as a single json key using '/'.
    # This syntax is equivalent to {"type":"Person", "affiliation": {"id":"https://www.grid.ac/institutes/grid.5333.6"}}
    
    filters = {"type":"Person", "affiliation/id": "https://www.grid.ac/institutes/grid.5333.6"}
    forge.search(filters)

* Added `ElasticSearch Terms <https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-terms-query.html>`__ query support when filter values are provided as a list and when ElasticSearch is used as a search endpoint `#306 <https://github.com/BlueBrain/nexus-forge/pull/306>`__.

.. code-block:: python

    # Filter by type using a dictionary
    filters = {"type":"Person", "affiliation/id": ["https://www.grid.ac/institutes/grid.5333.6","https://ror.org/02mrd0686"]}
    forge.search(filters, search_endpoint="elastic")

* Set "distribution.contentUrl" as default resource json property path to follow when collecting downloadable file urls. Set the current folder as the default download path `#265 <https://github.com/BlueBrain/nexus-forge/pull/265>`__.


.. code-block:: python

    # By default and when files downloads are described as distributions (https://nexus-forge.readthedocs.io/en/latest/interaction.html#dataset),
    # this release allows a client to move from:
    
    forge.download(Resource, follow="distribution.contentUrl", path=".")
    Dataset.download(forge, follow="distribution.contentUrl", path=".")

    # to simply:
    forge.download(Resource)
    Dataset.download()


Formattting
-----------

|Binder_Formatting| to try the enhancements.

* Updated forge.format() to know support URI rewriting. The specifiic rewriting logic is delegated to the configured Store.
  Two formatters are now supported:

  -  Formatter.STR: corresponds to configured (in the forge config file) str formatter
  
  -  Formatter.URI_REWRITER: URI rewriter. Using BlueBrainNexus store, this formatter will build a fully expanded _self rom a resource or file id 

.. code-block:: python

    forge.format(uri=resource.id, formatter=Formatter.URI_REWRITER, is_file=False, encoding=None) 



Bug Fixes
=========

Modeling
--------

* Bumped `rdflib` from `>=6.0.0` to `==6.2.0` to fix broken loading of JSON-LD context when using `core.commons.context.Context`. The error originated from an upstream rdflib bug (see rdflib issue `#2303 <https://github.com/RDFLib/rdflib/issues/2303>`__), `#295 <https://github.com/BlueBrain/nexus-forge/pull/295>`__ .

Querying
--------

* BlueBrainNexus store: fixed failing resource download when the downloadble URL is a _self `#283 <https://github.com/BlueBrain/nexus-forge/pull/283>`__ (issue `#282 <https://github.com/BlueBrain/nexus-forge/pull/282>`__) .
* BlueBrainNexus store: fixed download of a list of resources which were failing if at least one resource in the list did not have the requested content-type. Now only resources in the list with the requested content-type are downloaded `#283 <https://github.com/BlueBrain/nexus-forge/pull/283>`__ .

Resolving
---------

* Added `Graph` SPARQL clause to the query built by OntolgyResolver and AgentResolver to avoid retrieving an agent with more than one values for annotation properties (i.e name, familyName or givenName, label, ...) `#310 <https://github.com/BlueBrain/nexus-forge/pull/310>`__ (issue `#309 <https://github.com/BlueBrain/nexus-forge/pull/309>`__)

Storing
-------

* Store.upload() was failing when a configured file-to-resource-mapping.hjson file was definining a transformation rule based on a forge method because of an incorrect instanciation of a Mapper object (a None Forge object was provided) was provided `#315 <https://github.com/BlueBrain/nexus-forge/pull/315>`__ .

Changelog
=========

`Full changelog <https://github.com/BlueBrain/nexus-forge/compare/v0.8.0...v0.8.1>`__

.. |Binder_Resolving| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Querying
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F09%20-%20Resolving.ipynb

.. |Binder_Storing| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Storing
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F03%20-%20Storing.ipynb

.. |Binder_Formatting| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Formatting
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F08%20-%20Formatting.ipynb

.. |Binder_Querying| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Querying
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F04%20-%20Querying.ipynb

.. |Binder_Resource| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Resource
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F01%20-%20Resources.ipynb

.. |Binder_Resolving_UseCase| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Resource
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.1?filepath=examples%2Fnotebooks%2Fuse-cases%2FResolvingStrategies.ipynb
