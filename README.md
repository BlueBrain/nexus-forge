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

Forge initialization signature is:
```bash
KnowledgeGraphForge(configuration: Union[str, Dict], **kwargs)
```
where the `configuration` accepts a YAML file or a JSON dictionary, and `**kwargs` can
 be used to override the configuration provided for the Store.

The YAML configuration has the following structure:

```
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
```

and the python configuration would be like:

```
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
```
The required minimal configuration is:
* `name` for Model and Store
* `origin` and `source` for Model

See `kgforge/examples/configurations/` for YAML examples.

Create a forge instance:
```
forge = KnowledgeGraphForge("../path/to/configuration.yml")
```

**Resource**

A _Resource_ is an identifiable data object with a set of properties. It is mainly identified by its _Type_, 
which value is a concept, such as, Person, Contributor, Organisation, Experiment, etc. Reserved properties of a 
Resource are: `id`, `type` and `context`. 

Create a resource using keyword arguments or a JSON dictionary:

```bash
resource = Resource(name="Jane Doe", type="Person", email="jane.doe@examole.org")
```
or
```
data = {
    "name": "Jane Dow", 
    "type" : "Person", 
    "email" : "jane.doe@examole.org"
}
resource = Resource(data)
```

A resource can have files attached by assigning the output of `forge.attach` method to a property in the resource:

```bash
resource.picture = forge.attach("path/to/file.jpg")
```

**Dataset** 

A Dataset is a specialization of a `Resource` that provides users with operations to handle files 
and describe them with metadata. The metadata of `Datasets` refers specifically to, but not limited to:
* provenance: contribution (people or organizations that contributed to the creation of the Dataset), [generation](https://www.w3.org/TR/prov-o/#Generation) (links to resources used to generate this Dataset), [derivation](https://www.w3.org/TR/prov-o/#Derivation) (links another resource from which the Dataset is generated), [invalidation](https://www.w3.org/TR/prov-o/#Invalidation) (data became invalid)
* access: [distribution](https://schema.org/distribution) (a downloadable form of this Dataset, at a specific location, in a specific format)

The `Dataset` class provides methods for adding files to a `Dataset`. The added files will only be uploaded in the Store when the `forge.register` function is 
called on the Dataset so that the user flow is not slowed down and for efficiency purpose. We implemented this using 
the concept of `LazyAction`, which is a class that will hold an action that will be executed when required.

After the registration of the Dataset, a `DataDownload` resource will be created with some other automatically
extracted properties, such as  content type, size, file name, etc.
 
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

**Storing**

Storing allows us to persist and manage Resources in the configured Store. Resources contain additional
information in hidden properties to allow users recovering from errors:
* `_synchronized`, indicates that the last action succeeded
* `_last_action`, contains information about the last action that took place in the resource (e.g. register, update, etc.)
* `_store_metadata`, keeps additional resource metadata provided by the store such as version, creation date, etc. 

```bash
register(data: Union[Resource, List[Resource]]) -> None
update(data: Union[Resource, List[Resource]]) -> None
deprecate(data: Union[Resource, List[Resource]]) -> None
```

**Querying**

It is possible to retrieve resources from the store by (1) its id, (2) specifying filters with
the properties and a specific value and (3) using a simplified version of SPARQL query.

```bash
retrieve(id: str, version: Optional[Union[int, str]] = None) -> Resource
paths(type: str) -> PathsWrapper
search(*filters, **params) -> List[Resource]
sparql(query: str) -> List[Resource]
download(data: Union[Resource, List[Resource]], follow: str, path: str) -> None
```

**Versioning**

The user can create versions of Resources, if the Store supports this feature.

```bash
tag(data: Union[Resource, List[Resource]], value: str) -> None
freeze(data: Union[Resource, List[Resource]]) -> None
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

**Formatting**

A preconfigured set of string formats can be provided to ensure the consistency of data.

```bash
format(what: str, *args) -> str
```

**Resolving**

Resolvers are helpers to find commonly used resources that one may want to link to. For instance, one could have a set of pre-defined identifiers of Authors, and to make several references to the same Authors, a resolver can be used.

```bash
resolve(text: str, scope: Optional[str] = None, resolver: Optional[str] = None, target: Optional[str] = None, type: Optional[str] = None, strategy: ResolvingStrategy = ResolvingStrategy.BEST_MATCH) -> Optional[Union[Resource, List[Resource]]]
```

**Reshaping**

Reshaping allows trimming Resources by a specific set of properties.

```bash
reshape(data: Union[Resource, List[Resource]], keep: List[str], versioned: bool = False) -> Union[Resource, List[Resource]]
```

**Modeling**

To create _Resources_, the user can make use of Modeling functions. The user can explore 
predefined _Types_ and the properties that describe them via _Templates_. _Templates_ can be used
to create resources with the specified properties. Resources that 
are created using a template can be validated. 

```bash
context() -> Optional[Dict]
prefixes(pretty: bool = True) -> Optional[Dict[str, str]]
types(pretty: bool = True) -> Optional[List[str]]
template(type: str, only_required: bool = False) -> None
validate(data: Union[Resource, List[Resource]]) -> None
```

**Mapping**

Mappings are pre-defined configuration files that encode the logic on how to transform a specific 
data source into Resources that follow a template of a targeted _Type_. 
For instance, when different versions of the same dataset is regularly integrated, one can make 
use of Mappers to specify how the coming data is going to be integrated using the corresponding 
typed _Resource_. 

```bash
sources(pretty: bool = True) -> Optional[List[str]]
mappings(source: str, pretty: bool = True) -> Optional[Dict[str, List[str]]]
mapping(entity: str, source: str, type: Callable = DictionaryMapping) -> Mapping
map(data: Any, mapping: Union[Mapping, List[Mapping]], mapper: Callable = DictionaryMapper, na: Union[Any, List[Any]] = None) -> Union[Resource, List[Resource]]
```

### Archetypes

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

### Specializations

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

* DemoStore: a in-memory Store (do not use it in production)
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
