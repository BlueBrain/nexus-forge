=============
Release Notes
=============

Enhancements
============

Resolving
---------

|Binder_Resolving| and |Binder_Resolving_UseCase| to try.

* Enabled resolver mapping files to contain rules calling a forge method `#323 <https://github.com/BlueBrain/nexus-forge/pull/323>`__ (issue `#316 <https://github.com/BlueBrain/nexus-forge/issues/316>`__)
* More properties (e.g. altLabel, definition, isPartOf, ...) are retrieved when resolving an ontology term (`#337 <https://github.com/BlueBrain/nexus-forge/pull/337>`__)
* `alternateName` property can be used to resolve agent in AgentResolver `#404 <https://github.com/BlueBrain/nexus-forge/pull/404>`__
* `OntologyResolver`: Added an ontology resolver target 'Strain' `#405 <https://github.com/BlueBrain/nexus-forge/pull/405>`__

Querying
--------

|Binder_Querying| to try the enhancements.

* `BlueBrainNexus` store: An `elasticsearch or sparql view id <https://bluebrainnexus.io/docs/delta/api/views/index.html>`__ can be provided using a `view` argument when calling `forge.sparql`, `forge.elastic` or `forge.search` (`#373 <https://github.com/BlueBrain/nexus-forge/pull/373>`__)
  If a view id is provided, only data accessible from that view will be searched and retrieved. 
* `forge.elastic` can now return results as list of dict instead of a list of `Resource` when `as_resource` is set to False  `#382 <https://github.com/BlueBrain/nexus-forge/pull/382>`__


Forge
-----

|Binder_JSONLD| to try the enhancements.

* Bumped JSON-LD context version from 1.0 to 1.1 to enable expanding a JSON-LD prefix mapping ending with a non IRI-delimiting character such as '_' or any character not present in `rdflib.plugins.shared.jsonld.context.URI_GEN_DELIMS <https://github.com/RDFLib/rdflib/blob/959dec532a3844fde874a36c3ab2328f20b681cb/rdflib/plugins/shared/jsonld/context.py#L69>`__ (issue `#386 <https://github.com/BlueBrain/nexus-forge/issues/386>`__) `#387 <https://github.com/BlueBrain/nexus-forge/issues/387>`__ 
  See also `RDFLib/rdflib#2606 <https://github.com/RDFLib/rdflib/issues/2606>`__ 


Modeling
--------

|Binder_Modeling| to try the enhancements.

* `RdfModel`: Added support for importing ontologies from SHACL schemas using `owl:imports`. Added support for inference. Use `forge.validate(resource, inference="inference_value", type_='AType')` with `inference_value` as in `pyshacl <https://github.com/RDFLib/pySHACL/blob/v0.25.0/pyshacl/validate.py#L81>`__. `inference_value="rdfs"` is enough to extend the resource to validate with the transitive closures of type subClassOf and/or property subPropertyOf relations.
  Validation will fail when a type not in the resource to validate is provided as value of the `type_` argument unless inference is enabled (with `inference='rdfs'` for example) and the resource type is a subClassOf of the value of `type_` (issue `#369 <https://github.com/BlueBrain/nexus-forge/issues/369>`__) `#396 <https://github.com/BlueBrain/nexus-forge/pull/396>`__


Dataset
-------

|Binder_Dataset| to try the enhancements.

* Added `add_image` method to the `Dataset` class (issue `#388 <https://github.com/BlueBrain/nexus-forge/issues/388>`__ ) `#389 <https://github.com/BlueBrain/nexus-forge/issues/389>`__. This method will upload the image in the configured store and add an `image` property to the Dataset with the return dict as value made of at least the @id of the uploaded image.



Changelog
=========

`Full changelog <https://github.com/BlueBrain/nexus-forge/compare/v0.8.1...v0.8.2>`__

.. |Binder_Resolving| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Resolving
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.2?filepath=examples%2Fnotebooks%2Fgetting-started%2F09%20-%20Resolving.ipynb``

.. |Binder_Querying| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Querying
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.2?filepath=examples%2Fnotebooks%2Fgetting-started%2F04%20-%20Querying.ipynb

.. |Binder_Resolving_UseCase| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Resolving_UseCase
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.2?filepath=examples%2Fnotebooks%2Fuse-cases%2FResolvingStrategies.ipynb

.. |Binder_Modeling| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Modeling
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.2?filepath=examples%2Fnotebooks%2Fgetting-started%2F11%20-%20Modeling.ipynb

.. |Binder_Dataset| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_Dataset
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.2?filepath=examples%2Fnotebooks%2Fgetting-started%2F02%20-%20Datasets.ipynb

.. |Binder_JSONLD| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder_JSONLD
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/v0.8.2?filepath=examples%2Fnotebooks%2Fgetting-started%2F13%20-%20JSON-LD%20IO.ipynb
