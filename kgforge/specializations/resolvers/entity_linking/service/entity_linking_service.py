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
from abc import ABC, abstractmethod

from typing import List, Optional, Union, Any, Dict

from kgforge.core.commons.strategies import ResolvingStrategy
from kgforge.core.resource import encode
from kgforge.specializations.resources.entity_linking_candidate import EntityLinkingCandidate


class EntityLinkerService(ABC):

    def __init__(self, is_distance: bool = False):
        self.is_distance = is_distance

    @abstractmethod
    def generate_candidates(self, mentions: List[str], target:str, mention_context: Any, limit: int, bulk: bool)\
            -> Optional[List[EntityLinkingCandidate]]:
        pass

    def rank_candidates(self, candidates: List[EntityLinkingCandidate], strategy: ResolvingStrategy, threshold: float,
                        mention: str = None, mention_context: Any = None) -> Optional[List[Dict]]:

        exact_match_score = 0 if self.is_distance else 1
        threshold_operator = "<=" if self.is_distance else ">="
        is_sorted_reversed = True if not self.is_distance else False
        if strategy == ResolvingStrategy.EXACT_MATCH:
            zeros = [x for x in candidates if x.score == exact_match_score]
            if zeros and len(zeros) > 0:
                return [encode(zeros[0])]
            else:
                return None
        elif strategy == ResolvingStrategy.BEST_MATCH:
            chosen = sorted(candidates, key=lambda x: x.score, reverse=is_sorted_reversed)[0]
            return [encode(chosen)] if eval(f"{chosen.score} {threshold_operator} {threshold}") else None
        else:
            mentions = sorted(candidates, key=lambda x: x.score, reverse=is_sorted_reversed)
            return [encode(mention) for mention in mentions if eval(f"{mention.score} {threshold_operator} {threshold}")]
