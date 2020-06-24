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

from typing import Dict, List


def with_defaults(original: Dict, other: Dict, original_key: str, other_key: str,
                  keys: List[str]) -> None:
    """Update 'original' with 'other' 'keys' unless keys value is different in both dictionaries."""

    if original[original_key] == other[other_key]:
        for x in keys:
            if x not in original:
                original[x] = other[x]
