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

import asyncio
import copy
from difflib import context_diff
import json
import re
from pathlib import Path
from asyncio import Task
from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Callable, Dict, List, Optional, Union, Tuple
from urllib.error import URLError
from urllib.parse import quote_plus, urlparse

import nest_asyncio
import nexussdk as nexus
import requests
from aiohttp import ClientSession, hdrs
from numpy import nan
from requests import HTTPError

from kgforge.core import Resource
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import (
    _from_jsonld_one,
    recursive_resolve,
)
from kgforge.core.wrappings.dict import wrap_dict


class Service:

    def __init__(
        self,
        endpoint: str,
        model_context: Context,
        store_context: Context,
        max_connection: int,
        searchendpoints: Dict,
        content_type: str,
        accept: str,
        **params,
    ):

        self.endpoint = endpoint
        self.model_context = model_context
        self.context_cache: Dict = dict()
        self.context = store_context
        self.max_connection = max_connection
        self.params = copy.deepcopy(params)

        self.headers = {"Content-Type": content_type, "Accept": accept}

        try:
            sparql_config = searchendpoints["sparql"]
            self.headers_sparql = {
                "Content-Type": sparql_config["Content-Type"]
                if sparql_config and "Content-Type" in sparql_config
                else "text/plain",
                "Accept": sparql_config["Accept"]
                if sparql_config and "Accept" in sparql_config
                else "application/sparql-results+json",
            }

            self.sparql_endpoint = dict()
            self.sparql_endpoint["endpoint"] = searchendpoints["sparql"]["endpoint"]
            self.sparql_endpoint["type"] = "sparql"
        except Exception:
            raise ValueError(f"Store configuration error: sparql searchendpoint missing")