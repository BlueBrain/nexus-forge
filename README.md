[Installation](#installation) |
[Getting Started](#getting-started) |
[Contributing](#contributing) |
[Acknowledgements](#acknowledgements)

# Knowledge Graph Forge

A domain-agnostic, generic and extensible Python framework for **consistently**
building and interacting with knowledge graphs in a data science context.

This framework builds a **bridge** between data engineers, knowledge engineers,
and data scientists in the context of knowledge graphs by making easier for:

- **data engineers** to define, execute, and share data transformations in a traceable way,
- **knowledge engineers** to define and share knowledge representations of heterogeneous data,
- **data scientists** to query and register data during their analysis without
having to worry about the semantic formats and technologies,

while guaranteeing the consistency of operations with a **knowledge graph
schema** like [Neuroshapes](https://github.com/INCF/neuroshapes).

The architectural design choices:
 1) be generic on where it brings **flexibility** for adaptation to multiple ecosystems,
 2) be opinionated on where it simplifies the complexity,
 3) have a strong separation of concern with delegation to the lowest level for **modularity**.

## Installation

It is recommended to use a virtual environment such as [venv](https://docs.python.org/3.7/library/venv.html) or 
[conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html). 

Stable version

```bash
pip install kgforge
```

Upgrade to the latest version

```bash
pip install --upgrade kgforge
```

Development version

```bash
pip install git+https://github.com/BlueBrain/kgforge
```

## Getting Started

See in the directory `examples` for examples of usages, configurations, mappings. 

Make sure that the `jupyter notebook|lab` is launched in the same virtual environment where KGForge is installed. Alternatively, set up a specialized 
[kernel](https://ipython.readthedocs.io/en/stable/install/kernel_install.html).

### User API

**Forge** 

The forge is the main entry point to the features described next.

```bash
KnowledgeGraphForge(configuration: Union[str, Dict], **kwargs)
```

**Resources**

A _Resource_ is an identifiable data object with a set of properties. It is mainly identified by its _Type_, 
which is a concept, such as, Person, Contributor, Organisation, Experiment, etc. Automatically recognized properties of a Resource are: `id`, `type` and `context`. 

```bash
Resource(**properties)
```

**Dataset** 

A _Dataset_ is a specialization of a Resource that can have Files (or distributions) associated. It captures relevant metadata 
concerning its provenance.
 
```
Dataset(forge: KnowledgeGraphForge, type: str = "Dataset", **properties)
  add_parts(resources: List[Resource], versioned: bool = True) -> None
  add_distribution(path: str) -> None
  add_contribution(agent: str, **kwargs) -> None
  add_generation(**kwargs) -> None
  add_derivation(resource: Resource, versioned: bool = True, **kwargs) -> None
  add_invalidation(**kwargs) -> None
  add_files(path: str) -> None
  download(source: str, path: str) -> None
```

**Modeling**

To create _Resources_, the user can make use of Modeling functions. The user can explore available _Types_ and the properties that describe them via _Templates_. Resources that are created using a template can be validated. 

```bash
context() -> Optional[Dict]
prefixes(pretty: bool = True) -> Optional[Dict[str, str]]
types(pretty: bool = True) -> Optional[List[str]]
template(type: str, only_required: bool = False) -> None
validate(data: Union[Resource, List[Resource]]) -> None
```

**Resolving**

Resolvers are helpers to find commonly used resources that one may want to link to. For instance, one could have a set of pre-defined identifiers of Authors, and to make several references to the same Authors, a resolver can be used.

```bash
resolve(text: str, scope: Optional[str] = None, resolver: Optional[str] = None, target: Optional[str] = None, type: Optional[str] = None, strategy: ResolvingStrategy = ResolvingStrategy.BEST_MATCH) -> Optional[Union[Resource, List[Resource]]]
```

**Formatting**

A preconfigured set of string formats can be provided to ensure the consistency of data.

```bash
format(what: str, *args) -> str
```

**Mapping**

Mappings are pre-defined configuration files that encode the logic on how to transform a specific data source into Resources
that follow a template of a targeted Type. 
For instance, when different versions of the same dataset is regularly integrated, one can make use of Mappers to specify how the coming data is going to be integrated using the corresponding typed _Resource_. 

```bash
sources(pretty: bool = True) -> Optional[List[str]]
mappings(source: str, pretty: bool = True) -> Optional[Dict[str, List[str]]]
mapping(entity: str, source: str, type: Callable = DictionaryMapping) -> Mapping
map(data: Any, mapping: Union[Mapping, List[Mapping]], mapper: Callable = DictionaryMapper, na: Union[Any, List[Any]] = None) -> Union[Resource, List[Resource]]
```

**Reshaping**

Reshaping allows trimming Resources by a specific set of properties.

```bash
reshape(data: Union[Resource, List[Resource]], keep: List[str], versioned: bool = False) -> Union[Resource, List[Resource]]
```

**Querying**

To retrieve Resources from the Store, the following functions are available.

```bash
retrieve(id: str, version: Optional[Union[int, str]] = None) -> Resource:
paths(type: str) -> PathsWrapper:
search(*filters, **params) -> List[Resource]
sparql(query: str) -> List[Resource]
download(data: Union[Resource, List[Resource]], follow: str, path: str) -> None
```

**Storing**

Storing allows us to persist and manage Resources in the configured Store.

```bash
register(data: Union[Resource, List[Resource]]) -> None
update(data: Union[Resource, List[Resource]]) -> None
deprecate(data: Union[Resource, List[Resource]]) -> None
```

**Versioning**

If the store allows it the user can create versions of Resources.

```bash
tag(data: Union[Resource, List[Resource]], value: str) -> None
freeze(data: Union[Resource, List[Resource]]) -> None
```

**Files handling**

A resource can have files attached. This is a lower level of _Dataset_ usage. 

```bash
attach(path: str) -> LazyAction
```

**Converting**

To use Resources with other libraries such as pandas, different data conversion functions are available.

```bash
as_json(data: Union[Resource, List[Resource]], expanded: bool = False, store_metadata: bool = False) -> Union[Dict, List[Dict]]
as_jsonld(data: Union[Resource, List[Resource]], compacted: bool = True, store_metadata: bool = False) -> Union[Dict, List[Dict]]
as_triples(data: Union[Resource, List[Resource]], store_metadata: bool = False) -> List[Tuple[str, str, str]]
as_dataframe(data: List[Resource], na: Union[Any, List[Any]] = [None], nesting: str = ".", expanded: bool = False, store_metadata: bool = False) -> DataFrame
from_json(data: Union[Dict, List[Dict]], na: Union[Any, List[Any]] = None) -> Union[Resource, List[Resource]]
from_jsonld(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]
from_triples(data: List[Tuple[str, str, str]]) -> Union[Resource, List[Resource]]
from_dataframe(data: DataFrame, na: Union[Any, List[Any]] = np.nan, nesting: str = ".") -> Union[Resource, List[Resource]]
```

### Internals

The framework provides a set of archetypes that allows the extension of the different _Forge_ modules to work with different technologies. These are described next.

Mapper

The Mapper provides the interface to a technology to be used to do the transformation of data.

```bash
Mapper(forge: Optional["KnowledgeGraphForge"] = None)
  map(data: Any, mapping: Union[Mapping, List[Mapping]], na: Union[Any, List[Any]]) -> Union[Resource, List[Resource]]
```

Mapping

The mapping interface provides the interfaces to load and serialize mapping files.

```bash
Mapping(mapping: str)
  load(source: str) -> Mapping
  save(path: str) -> None
```

Model

The Model provides the interface for data modeling technologies to be implemented.

```bash
Model(source: str, **source_config)
  prefixes(pretty: bool) -> Optional[Dict[str, str]]
  types(pretty: bool) -> Optional[List[str]]
  template(type: str, only_required: bool) -> str
  sources(pretty: bool) -> Optional[List[str]]
  mappings(source: str, pretty) -> Optional[Dict[str, List[str]]]
  mapping(entity: str, source: str, type: Callable) -> Mapping
  validate(data: Union[Resource, List[Resource]]) -> None
```

Resolver

```bash
Resolver(source: str, targets: List[Dict[str, str]], result_resource_mapping: str, **source_config)
  resolve(text: str, target: Optional[str], type: Optional[str], strategy: ResolvingStrategy) -> Optional[Union[Resource, List[Resource]]]
```

Store

The Store provides the interface of storage for different technologies to be implemented.

```bash
Store(endpoint: Optional[str] = None, bucket: Optional[str] = None, token: Optional[str] = None, versioned_id_template: Optional[str] = None, file_resource_mapping: Optional[str] = None))
  register(data: Union[Resource, List[Resource]]) -> None
  upload(path: str) -> Union[Resource, List[Resource]]
  retrieve(id: str, version: Optional[Union[int, str]]) -> Resource
  download(data: Union[Resource, List[Resource]], follow: str, path: str) -> None
  update(data: Union[Resource, List[Resource]]) -> None
  tag(data: Union[Resource, List[Resource]], value: str) -> None
  deprecate(data: Union[Resource, List[Resource]]) -> None
  search(resolvers: List[Resolver], *filters, **params) -> List[Resource]
  sparql(prefixes: Dict[str, str], query: str) -> List[Resource]
  freeze(data: Union[Resource, List[Resource]]) -> None
```

**Archetype specializations**

The following implementation of the above archetypes are (or will) be available as part of this repository. 

Mappers

* DictionaryMapper
* [TODO] R2RmlMapper
* [TODO] ResourceMapper
* [TODO] TableMapper


Mappings

* DictionaryMapping

Models

* DemoModel
* RdfModel: currently supports [SHACL](https://www.w3.org/TR/shacl/) shapes.

Resolvers

* DemoResolver

Stores

* DemoStore
* [BlueBrainNexus](https://github.com/BlueBrain/nexus)
* [TODO] RdfLibGraph 


## Contributing

Please add `@pafonta` as a reviewer if your Pull Request modifies `core`.

Setup

```bash
git clone https://github.com/BlueBrain/kgforge
pip install --editable kgforge[dev]
```

Checks before committing

```bash
tox
```

### Styling

[PEP 8](https://www.python.org/dev/peps/pep-0008/),
[PEP 257](https://www.python.org/dev/peps/pep-0257/), and
[PEP 20](https://www.python.org/dev/peps/pep-0020/) must be followed.

### Releasing

```bash
# Setup
pip install --upgrade pip setuptools wheel twine

# Checkout
git checkout master
git pull upstream master

# Check
tox

# Tag
git tag -a v<x>.<y>.<z> HEAD
git push upstream v<x>.<y>.<z>

# Build
python setup.py sdist bdist_wheel

# Upload
twine upload dist/*

# Clean
rm -R build dist *.egg-info
```

## Acknowledgements

This project has received funding from the EPFL Blue Brain Project (funded by
the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology)
and from the European Union’s Horizon 2020 Framework Programme for Research and
Innovation under the Specific Grant Agreement No. 785907 (Human Brain Project SGA2).
