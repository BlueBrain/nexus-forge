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

from typing import Any, Dict


class DictWrapper(dict):

    # TODO Should be immutable. DKE-146.

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    # No need to define __repr__ and __str__ as the ones from dict are suitable.


def wrap_dict(data: Dict) -> DictWrapper:
    if isinstance(data, Dict):
        return _wrap(data)
    else:
        raise TypeError("not a dictionary")


def _wrap(data: Any) -> Any:
    if isinstance(data, Dict):
        return DictWrapper({k: _wrap(v) for k, v in data.items()})
    else:
        return data
