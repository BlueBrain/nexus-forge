Specializations
===============

The following implementation of the archetypes are available as part of Nexus Forge.

Resources
---------

* Dataset: `kgforge.core.specializations.resources.dataset.Dataset`
* EntityLinkingCandidate: `kgforge.core.specializations.resources.entity_linking_candidate.EntityLinkingCandidate`


Mappers
-------

* DictionaryMapper: `kgforge.core.specializations.mappers.dictionaries.DictionaryMapper`


Mappings
--------

* DictionaryMapping: `kgforge.core.specializations.mappings.dictionaries.DictionaryMapping`

Models
------

* DemoModel: `kgforge.core.specializations.models.demo_model.DemoModel`
* RdfModel: currently supports `W3C SHACL <https://www.w3.org/TR/shacl/>`__ schemas (`kgforge.core.specializations.models.rdf_model.RdfModel`).

Resolvers
---------

* DemoResolver: `kgforge.core.specializations.resolvers.demo_resolver.DemoResolver`
* OntologyResolver: `kgforge.core.specializations.resolvers.ontology_resolver.OntologyResolver`
* AgentResolver: `kgforge.core.specializations.resolvers.agent_resolver.AgentResolver`
* EntityLinkerElastic: `kgforge.core.specializations.resolvers.entity_linking.entity_linker_elastic.EntityLinkerElastic`
* EntityLinkerSkLearn: `kgentitylinkingsklearn.entity_linking_sklearn.EntityLinkerSkLearn`

Stores
------

* DemoStore: a in-memory Store (do not use it in production) (`kgforge.core.specializations.stores.demo_store.DemoStore`)
* `BlueBrainNexus <https://github.com/BlueBrain/nexus>`__: `kgforge.core.specializations.stores.bluebrain_nexus.BlueBrainNexus`
