=============
Release Notes
=============

This release adds new features and enhancements to Nexus Forge as well as bug fixes.

New Features
============

Resolving
---------

* Added ontology resource resolving based on skos:prefLabel and skos:altLabel in addition to label and skos:notation. `#245 <https://github.com/BlueBrain/nexus-forge/pull/245>`__ (|Binder_Resolving| to try it)

Modeling
--------

* Add support for validation against a schema. `#217 <https://github.com/BlueBrain/nexus-forge/pull/217>`__ (|Binder_Modeling| to try it)

.. code-block:: python

    from kgforge.core import KnowledgeGraphForge
    # see https://github.com/BlueBrain/nexus-forge/blob/master/examples/notebooks/use-cases/prod-forge-nexus.yml for a full forge config example.
    forge = KnowledgeGraphForge(configuration="./config.yml", **kwargs)
    person = Resource(type="Person", name="Jane Doe")
    # By default the schema associated with the resource type is picked for validation. A different type can be set using the type_ argument.
    forge.validate(person, type_="Agent")


Enhancements
============

Querying
--------

|Binder_Querying| to try the querying enhancements.

* Added support for searching using filters (except when Paths syntax is used) from _store_metadata properties (i.e _createdAt, _updatedAt,...) `#224 <https://github.com/BlueBrain/nexus-forge/pull/224>`__ `#240 <https://github.com/BlueBrain/nexus-forge/pull/240>`__ (issue `#209 <https://github.com/BlueBrain/nexus-forge/pull/209>`__)
* Added support for searching using datetime filters which can be specify as string suffixed with `^^xsd:dateTime` `#224 <https://github.com/BlueBrain/nexus-forge/pull/224>`__

.. code-block:: python

    from kgforge.core import KnowledgeGraphForge
    # see https://github.com/BlueBrain/nexus-forge/blob/master/examples/notebooks/use-cases/prod-forge-nexus.yml for a full forge config example.
    forge = KnowledgeGraphForge(configuration="./config.yml", **kwargs)
    filters = {
           "type": "Dataset",
           "_createdAt":'"2022-04-12T21:29:14.410Z"^^xsd:dateTime'
          }
    forge.search(filters)


* Added support for disabling SPARQL rewriting when a correct SPARQL is provided `#224 <https://github.com/BlueBrain/nexus-forge/pull/224>`__ (issue `#218 <https://github.com/BlueBrain/nexus-forge/pull/218>`__)
* Inline query limit/offset arguments are now superseded by limit/offset provided as argument for `forge.search()` `#224 <https://github.com/BlueBrain/nexus-forge/pull/224>`__ (issue `#189 <https://github.com/BlueBrain/nexus-forge/pull/189>`__)
* Added support for `IN` SPARQL clause when rewriting SPARQL queries in `forge.search()` `#240 <https://github.com/BlueBrain/nexus-forge/pull/240>`__ (issue `#242 <https://github.com/BlueBrain/nexus-forge/pull/242>`__)
* Using filters as argument when calling `forge.search(*filters, **params)` now raises an exception `#240 <https://github.com/BlueBrain/nexus-forge/pull/240>`__
* When using BlueBrainNexusStore, `forge.retrieve()` and `forge.search()` now get the `original registered JSON payload <https://bluebrainnexus.io/docs/delta/api/resources-api.html#fetch-original-payload>`__ to avoid any JSON transformation `#232 <https://github.com/BlueBrain/nexus-forge/pull/232>`__
* `forge.search()` returns resources at the exact revision they are stored in the configured searchendpoint and no longer at the latest revision. As a consequence search results are no longer `_sychronized` `#232 <https://github.com/BlueBrain/nexus-forge/pull/232>`__
* `_last_action` property is now added to resources obtained from `forge.retrieve()` `#232 <https://github.com/BlueBrain/nexus-forge/pull/232>`__
* Added the property distribution.atLocation.store.type and distribution.atLocation.store.type._rev to BlueBrainNexusStore file metadata mapping file `#232 <https://github.com/BlueBrain/nexus-forge/pull/232>`__
* When using BlueBrainNexusStore, it is possible to set (in the forge config file) GET params when calling `forge.retrieve() `#232 <https://github.com/BlueBrain/nexus-forge/pull/232>`__

Converting
----------

|Binder_JSON-LD-IO| to try the JSON-LD enhancements.

* `forge.as_jsonld(r, form="expanded")` now outputs expanded JSON-LD with @value added for literals. `#244 <https://github.com/BlueBrain/nexus-forge/pull/244>`__
* `forge.as_jsonld(r, form="compacted")` keeps unchanged JSON null values and arrays. The param `array_as_set` is no longer needed and is thus removed along with the `na` argument `#244 <https://github.com/BlueBrain/nexus-forge/pull/244>`__


Resolving
---------

|Binder_Resolving| to try the resolving enhancements.

* Added `searchendpoints` config in the `forge config Resolvers section <https://github.com/BlueBrain/nexus-forge/blob/v0.7.1/examples/notebooks/use-cases/prod-forge-nexus.yml#L30>`__ `#226 <https://github.com/BlueBrain/nexus-forge/pull/226>`__


Bug Fixes
=========

* Added an identifier and the forge model configured JSON-LD context to resources obtained from an ElasticSearch query `#238 <https://github.com/BlueBrain/nexus-forge/pull/238>`__ (issue `#230 <https://github.com/BlueBrain/nexus-forge/pull/230>`__) (|Binder_Querying| to try it)
* Fixed failing SPARQL query rewriting when a used JSON-LD context term does not have `@id` `#231 <https://github.com/BlueBrain/nexus-forge/pull/231>`__

Changelog
=========

`Full changelog <https://github.com/BlueBrain/nexus-forge/compare/v0.7.0...v0.7.1>`__

.. |Binder_Resolving| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Querying
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.7.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F09%20-%20Resolving.ipynb

.. |Binder_Modeling| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Modeling
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.7.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F09%20-%20Modeling.ipynb

.. |Binder_JSON-LD-IO| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_JSON-LD-IO
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.7.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F13%20-%20JSON-LD%20IO.ipynb

.. |Binder_Querying| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Querying
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.7.1?filepath=examples%2Fnotebooks%2Fgetting-started%2F04%20-%20Querying.ipynb
