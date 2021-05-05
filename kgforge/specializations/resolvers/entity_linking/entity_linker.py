# 
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.
from abc import ABCMeta
from typing import Dict, List, Optional, Tuple, Union, Any

from kgforge.core import Resource
from kgforge.core.archetypes import Resolver
from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.exceptions import ResolvingError
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.strategies import ResolvingStrategy


class EntityLinker(Resolver, metaclass=ABCMeta):

    def __init__(self, source: str, targets: List[Dict[str, str]], result_resource_mapping: str,
                 **source_config) -> None:
        super().__init__(source, targets, result_resource_mapping, **source_config)

    def _resolve(self, text: Union[str, List[str]], target: str, type: str,
                 strategy: ResolvingStrategy, resolving_context: Any, limit: Optional[str],
                 threshold: Optional[float]) -> Optional[List[Tuple[str, List[Dict]]]]:
        if target is not None:
            if isinstance(self.service, dict):
                entity_linker_service = self.service[target]
            else:
                entity_linker_service = self.service
        else:
            raise ResolvingError("A target is required for Entity Linker.")
        if isinstance(entity_linker_service, LazyAction):
            entity_linker_service = entity_linker_service.execute()
            self.service[target] = entity_linker_service
        mentions = [text] if isinstance(text, str) else text
        candidates = entity_linker_service.generate_candidates(mentions=mentions, target=target, mention_context=resolving_context,
                                                               limit=limit, bulk=False)
        return [(m, entity_linker_service.rank_candidates(candidates=cl, strategy=strategy, threshold=threshold,
                                                          mention=m, mention_context=resolving_context)) for m, cl in candidates]
