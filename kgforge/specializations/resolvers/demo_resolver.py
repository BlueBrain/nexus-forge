import json
from pathlib import Path

from kgforge.core.commons.typing import ManagedData
from kgforge.core.modeling.resolvers import (OntologyConfiguration, OntologyResolver,
                                             ResolvingStrategy)
from kgforge.specializations.mappers.dictionaries import DictionaryMapper
from kgforge.specializations.mappings.dictionaries import DictionaryMapping


class DemoResolver(OntologyResolver):

    def __init__(self, configuration: OntologyConfiguration) -> None:
        super().__init__()
        self.name = configuration.name
        # TODO Example for 'Ontology term to resource mapping could be loaded from a Hjson string or an URL'.
        self.term_resource_mapping = DictionaryMapping.load(configuration.term_resource_mapping)
        with Path(configuration.source).open() as f:
            self.ontology = json.load(f)

    def resolve(self, label: str, type: str, strategy: ResolvingStrategy) -> ManagedData:
        resolved = [(len(x["label"]) - len(label), x) for x in self.ontology if label in x["label"]]
        ordered = sorted(resolved, key=lambda x: x[0])
        if strategy == ResolvingStrategy.BEST_MATCH:
            selected = ordered[0][1]
        else:
            selected = [x[1] for x in ordered]
        return DictionaryMapper(None).map(selected, self.term_resource_mapping)
