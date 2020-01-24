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


def with_defaults(original: Dict, other: Dict, key: str, keys: List[str]) -> None:
    """Update 'original' with 'other' 'keys' unless 'key' is different in both dictionaries."""
    cond = original[key] == other[key]
    for x in keys:
        if cond or x not in original:
            original[x] = other[x]
