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


from logging import exception
import copy
import json
from pathlib import Path
from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Callable, Dict, List, Optional, Union, Tuple
from urllib.error import URLError
from urllib.parse import quote_plus, urlparse

import requests
from numpy import nan
from requests import HTTPError

from kgforge.core import Resource
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import DownloadingError
from kgforge.core.conversions.rdf import (
    _from_jsonld_one,
    recursive_resolve,
)
from kgforge.core.wrappings.dict import DictWrapper, wrap_dict
from kgforge.specializations.databases.utils import resources_from_request
from kgforge.specializations.stores.bluebrain_nexus import _error_message


class WebService:

    def __init__(
        self,
        endpoint: str,
        model_context: Context,
        service_context: Context,
        max_connection: int,
        content_type: str,
        accept: str,
        **params,
    ):

        self.endpoint = endpoint
        self.model_context = model_context
        self.context_cache: Dict = dict()
        self.context = service_context
        self.max_connection = max_connection
        self.files_download = params.pop('files_download', None)
        self.params = copy.deepcopy(params)

        self.headers = {"Content-Type": content_type, "Accept": accept}

        self.headers_download = {
            "Content-Type": self.files_download["Content-Type"]
            if self.files_download and "Content-Type" in self.files_download
            else "text/plain",
            "Accept": self.files_download["Accept"]
            if self.files_download and "Accept" in self.files_download
            else "text/plain",
        }

    def search(self, resolvers, *filters, **params):
        # resolvers are not used, just passed because of previous methods shapes
        filter_params = filters[0]
        if not isinstance(filter_params, dict):
            raise NotImplementedError('Currently only the use of a dictionary is implemented')
        query_params = {**filter_params, **params}
        return resources_from_request(self.endpoint, self.headers, **query_params)