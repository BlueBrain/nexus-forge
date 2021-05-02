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

import pickle
from pathlib import Path
from typing import Optional, Union, List

import numpy as np

from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.specializations.resolvers.entity_linking.service.entity_linking_service import EntityLinkerService
from kgforge.specializations.resources import EntityLinkingCandidate


class EntityLinkerServiceSkLearn(EntityLinkerService):

    def __init__(self, kb, aliases, model, index):
        super().__init__(is_distance=True)
        self.kb = kb
        self.aliases = aliases
        self.model = model
        self.index = index

    def generate_candidates(self, mentions, target, mention_context, limit, bulk) \
            -> Optional[Union[EntityLinkingCandidate, List[EntityLinkingCandidate]]]:

        def _(d, i):
            alias, uid = self.aliases[int(i)]
            label, definition = self.kb[uid]
            return EntityLinkingCandidate(d, label=label, altLabel=alias, id=uid, definition=definition)

        mentions_index = [(i, str(mention)) for i, mention in enumerate(mentions)]
        mentions_labels = {str(mention) for mention in mentions}
        embeddings = self.model.transform(mentions_labels)

        distances, indexes = self.index.kneighbors(embeddings, limit)
        results = np.stack((distances, indexes), axis=2)
        i_res = {m: [_(d, i) for d, i in rs] for m, rs in zip(mentions_labels, results)}
        return [(m, i_res[m]) for i, m in mentions_index]

    @staticmethod
    def from_pretrained(dirpath: Path, filename):
        filepath = dirpath / filename
        if filepath.is_file():
            with filepath.open(mode='rb') as f:
                kb = pickle.load(f)
                aliases = pickle.load(f)
                model = pickle.load(f)
                index = pickle.load(f)
                return EntityLinkerServiceSkLearn(kb, aliases, model, index)
        else:
            raise ConfigurationError(f"{dirpath}/{filename} is not a valid file path")
