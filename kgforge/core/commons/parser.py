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

import dateutil
import datetime
from dateutil.parser import ParserError


def _parse_type(value: Any):

    try:
        # integer
        if str(value).isnumeric():
            return int
        # bool
        if value is True or value is False:
            return bool
        # double
        if float(value):
            return float
    except ValueError as ve:
        pass
    except TypeError as te:
        pass
    try:
        # Date
        if isinstance(dateutil.parser.parse(str(value)), datetime.datetime):
            return datetime.datetime
    except ParserError as pe:
        return str
