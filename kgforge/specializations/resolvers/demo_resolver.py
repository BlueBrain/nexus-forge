# 
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

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
