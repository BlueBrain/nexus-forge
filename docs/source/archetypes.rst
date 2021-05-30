Archetypes
==========

The framework provides a set of archetypes that allows the extension of the different Nexus Forge modules to work with
different technologies. These are described next.

Mapper
------

The Mapper archetype defines an interface for transforming to a `Resource` or list of Resources data from different sources and of different formats.

.. code-block:: python

   Mapper(forge: Optional["KnowledgeGraphForge"] = None)
     map(data: Any, mapping: Union[Mapping, List[Mapping]], na: Union[Any, List[Any]]) -> Union[Resource, List[Resource]]

Mapping
-------

The Mapping archetype defines an interface for loading (from a file, a str or a URL) and serializing mapping rules.
Mappings are declarative rules encoding the logic of transforming data from a given source and format into resources.

.. code-block:: python

   Mapping(mapping: str)
     load(source: str) -> Mapping
     save(path: str) -> None

Model
-----

The Mapping archetype defines an interface for data modeling (e.g. W3C SHACL or JSON schemas) technologies to be used for
(meta)data validation.

.. code-block:: python

   Model(source: str, **source_config)
     prefixes(pretty: bool) -> Optional[Dict[str, str]]
     types(pretty: bool) -> Optional[List[str]]
     template(type: str, only_required: bool) -> str
     sources(pretty: bool) -> Optional[List[str]]
     mappings(source: str, pretty) -> Optional[Dict[str, List[str]]]
     mapping(entity: str, source: str, type: Callable) -> Mapping
     validate(data: Union[Resource, List[Resource]]) -> None

Resolver
--------

The Resolver archetype defines an interface for linking (or resolving) str, list of str or a `Resource` to identifiers
(URIs) in a knowledge base (e.g. ontologies, knowledge graph).

.. code-block:: python

   Resolver(source: str, targets: List[Dict[str, str]], result_resource_mapping: str, **source_config)
     resolve(text: Union[str, List[str], Resource], target: str, type: str,
                strategy: ResolvingStrategy, resolving_context: Any, property_to_resolve: str, merge_inplace_as: str,
                limit: int, threshold: float) -> Optional[Union[Resource, List[Resource], Dict[str, List[Resource]]]]:

Store
-----

The Store archetype defines an interface for (meta)data storage, search, download, deprecation and tag.

.. code-block:: python

   Store(endpoint: Optional[str] = None, bucket: Optional[str] = None, token: Optional[str] = None, versioned_id_template: Optional[str] = None, file_resource_mapping: Optional[str] = None))
     register(data: Union[Resource, List[Resource]]) -> None
     upload(path: str) -> Union[Resource, List[Resource]]
     retrieve(id: str, version: Optional[Union[int, str]], cross_bucket: bool) -> Resource
     download(data: Union[Resource, List[Resource]], follow: str, path: str, overwrite: bool) -> None
     update(data: Union[Resource, List[Resource]]) -> None
     tag(data: Union[Resource, List[Resource]], value: str) -> None
     deprecate(data: Union[Resource, List[Resource]]) -> None
     search(resolvers: List[Resolver], *filters, **params) -> List[Resource]
     sparql(prefixes: Dict[str, str], query: str) -> List[Resource]
     elastic(query: str, debug: bool, limit: int, offset: int) -> List[Resource]:
     freeze(data: Union[Resource, List[Resource]]) -> None
