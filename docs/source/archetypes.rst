Archetypes
==========

The framework provides a set of archetypes that allows the extension of the different *Forge* modules to work with different technologies. These are described next.

Mapper
------

The Mapper provides the interface to a technology to be used to do the transformation of data.

.. code-block:: python

   Mapper(forge: Optional["KnowledgeGraphForge"] = None)
     map(data: Any, mapping: Union[Mapping, List[Mapping]], na: Union[Any, List[Any]]) -> Union[Resource, List[Resource]]

Mapping
-------

The mapping interface provides the interfaces to load and serialize mapping files.

.. code-block:: python

   Mapping(mapping: str)
     load(source: str) -> Mapping
     save(path: str) -> None

Model
-----

The Model provides the interface for data modeling technologies to be implemented.

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

.. code-block:: python

   Resolver(source: str, targets: List[Dict[str, str]], result_resource_mapping: str, **source_config)
     resolve(text: str, target: Optional[str], type: Optional[str], strategy: ResolvingStrategy) -> Optional[Union[Resource, List[Resource]]]

Store
-----

The Store provides the interface of storage for different technologies to be implemented.

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
     freeze(data: Union[Resource, List[Resource]]) -> None
