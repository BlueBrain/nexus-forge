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
import itertools

import requests

from typing import Callable, Dict, List, Optional, Union, Any

from kgforge.core.archetypes import Store
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.resolvers.entity_linking.service.entity_linking_service import EntityLinkerService
from kgforge.specializations.resources.entity_linking_candidate import EntityLinkingCandidate


class EntityLinkerElasticService(EntityLinkerService):

    def __init__(self, store: Callable, targets: Dict[str, str], encoder, result_resource_mapping, **store_config):
        super().__init__(is_distance=False)
        self.sources: Dict[str, Store] = dict()
        for target, bucket in targets.items():
            store_config.update(bucket=bucket)
            self.sources[target] = store(**store_config)
        self.encoder = encoder
        self.result_mapping: Any = self.mapping.load(result_resource_mapping)

    @property
    def mapping(self) -> Callable:
        return DictionaryMapping

    @property
    def mapper(self) -> Callable:
        return DictionaryMapper

    def generate_candidates(self, mentions, target, mention_context, limit, bulk) -> Optional[Union[EntityLinkingCandidate, List[EntityLinkingCandidate]]]:

        def _(d, resource):
            return EntityLinkingCandidate(d, **resource)

        mentions_index = [(i, str(mention)) for i, mention in enumerate(mentions)]
        mentions_labels = {str(mention) for mention in mentions}

        resources, scores = [], []
        for mention in mentions_labels:
            call_url = self.encoder.format(x=mention)
            embedding_object = requests.get(url=call_url)
            embedding = self.mapper().map(embedding_object.json(), self.result_mapping, None)
            if embedding is not None and hasattr(embedding, "embedding"):
                mention_resources, mention_resources_scores = self._similar(embedding.embedding, target, limit)
                resources.append(mention_resources)
                scores.append(mention_resources_scores)
        i_res = {m: [_(scores[j][i], resource) for i, resource in enumerate(rs)] for j, (m, rs) in
                 enumerate(zip(itertools.cycle(mentions_labels), resources))}
        return [(m, i_res[m]) for i, m in mentions_index if m in i_res]

    def _similar(self, item_embedding, target, limit, offset=0):
        """
        Given a vector, find similar top [limit] resources, ranked by cosine similarity
        """

        query = """{
            "size": %s,
            "_source": {
                "exclude": ["embedding"]
            },
            "query": {
                "script_score": {
                    "query": {
                        "exists": {
                            "field": "embedding"
                        }
                    },
                    "script": {
                        "source": "doc['embedding'].size() == 0 ? 0 : (cosineSimilarity(params.queryVector, doc['embedding'])+1.0) / 2",
                        "params": {
                            "queryVector": %s
                        }
                    }
                }
            }
        }""" % (limit, item_embedding)
        resources = self.sources[target].elastic(query, False, limit=limit, offset=offset)
        if len(resources) > 0:
            scores = [r._score for r in resources if hasattr(r, "_score")]
            return [dict(r._source) for r in resources if hasattr(r, "_source")], scores
        else:
            return None
