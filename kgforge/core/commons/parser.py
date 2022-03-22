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
from rdflib import Literal, XSD
from typing import Any

import dateutil
import datetime
from dateutil.parser import ParserError


def _parse_type(value: Any, parse_str:bool = False):
    _type = type(value)
    try:
        if _type == str and parse_str:
            # integer
            if value.isnumeric():
                return int, value
            # double
            if float(value):
                return float, value

    except ValueError as ve:
        pass
    except TypeError as te:
        pass
    try:
        # always parse str for datetime. TODO: find a better way of parsing datetime literal
        if _type == str and ("^^<http://www.w3.org/2001/XMLSchema#dateTime>" in value or "^^xsd:dateTime" in value):
            # Datetime => example="2011-04-09T20:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime>
            value_parts = value.split("^^")
            parsed_value = value_parts[0]
            return datetime.datetime, parsed_value
        else:
            return _type,value
    except Exception as pe:
        return _type, value
