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
from typing import Any

from kgforge.core import Resource


class EntityLinkingCandidate(Resource):

    def __init__(self, score, candidate_context:Any = None, **properties):
        self.score = score
        self.candidate_context = candidate_context
        super().__init__(**properties)

    def __repr__(self):
        attrs = (f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Candidate({', '.join(attrs)})"
