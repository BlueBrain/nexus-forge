from typing import Dict, List

from kgforge.core.modeling.resolvers import (OntologyConfiguration, OntologyResolver,
                                             ResolvingStrategy)
from kgforge.core.resources import Resource


class OntologiesHandler:

    def __init__(self, configurations: List[OntologyConfiguration]) -> None:
        self._configurations = {x.name: x for x in configurations}
        self._resolvers: Dict[str, OntologyResolver] = {}

    def resolve(self, label: str, ontology: str, type: str = "Class",
                strategy: ResolvingStrategy = ResolvingStrategy.BEST_MATCH) -> Resource:
        try:
            resolver = self._resolvers[ontology]
        except KeyError:
            config = self._configurations[ontology]
            resolver = config.resolver(config)
            self._resolvers[ontology] = resolver
        finally:
            return resolver.resolve(label, type, strategy)
