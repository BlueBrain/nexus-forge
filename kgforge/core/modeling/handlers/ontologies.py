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
