from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Callable, NamedTuple, Union

from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import FilePath, Hjson, ManagedData, URL
from kgforge.core.storing.store import Store


class OntologyConfiguration(NamedTuple):
    # Ontologies are identified by a name. It is used by users in resolve().
    name: str
    # Some ontologies could have different source data.
    # Ontology data could be loaded from a file, an URL, or the store.
    source: Union[FilePath, URL, Store]
    # Some ontologies could have their terms resolved differently.
    # Ontology resolver is a derived class of OntologyResolver.
    resolver: Callable
    # Some ontologies could have their resolved terms in different formats.
    # Ontology term to resource mapping could be loaded from a Hjson string, a file, or an URL.
    term_resource_mapping: Union[Hjson, FilePath, URL]


class ResolvingStrategy(Enum):
    ALL = auto()
    BEST_MATCH = auto()


class OntologyResolver(ABC):

    def __init__(self) -> None:
        # POLICY Specializations should have 'configuration: OntologyConfiguration' in their __init__().
        # POLICY Ontology data access could be lazy: no general loading at object creation.
        # POLICY There could be caching but it should be aware of changes made in the source.
        pass

    @catch
    @abstractmethod
    def resolve(self, label: str, type: str, strategy: ResolvingStrategy) -> ManagedData:
        # POLICY With ResolvingStrategy.BEST_MATCH, returns a (unique) Resource.
        # POLICY Use already defined mappers, if possible, to map returned data to a resource.
        # POLICY Use configuration.term_resource_mapping to know how to do it.
        pass
