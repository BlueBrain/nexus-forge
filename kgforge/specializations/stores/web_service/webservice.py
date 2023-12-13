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
import copy
import requests
from typing import Dict, Optional

from kgforge.core.resource import Resource
from kgforge.core.commons.parser import _process_types
from kgforge.core.commons.exceptions import ConfigurationError, QueryingError


class WebService:

    def __init__(
        self,
        endpoint: str,
        content_type: str,
        accept: str,
        response_location : Optional[str] = None,
        files_download: Optional[Dict] = None,
        searchendpoints : Optional[Dict] = None,
        health_endpoint: Optional[str] = None,
        **params,
    ):
        """A Web service"""
        self.endpoint = endpoint
        self.context_cache: Dict = dict()
        self.response_location = response_location
        self.files_download = files_download
        self.health_endpoint = health_endpoint
        self.searchendpoints = searchendpoints
        if self.searchendpoints:
            for endpoint in self.searchendpoints:
                if not 'endpoint' in self.searchendpoints[endpoint]:
                    raise ConfigurationError(f"Missing endpoint searchenpoints")
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
        self.max_connection = params.pop('max_connection', None)
        
    @staticmethod
    def resources_from_request(url: str,
                               headers: Dict,
                               response_location: Dict,
                               **request_params):
        """Perform a HTTP request

        :param headers: The headers to be passed to the request
        :param response_loc: The nested location of the relevat metadata in the
            response. Example: NeuroMorpho uses response["_embedded"]["neuronResources"]
            which should be given as: response_loc = ["_embedded", "neuronResources"]
        :param request_params: Any other parameter for the request
        """
        try:
            response = requests.get(url, params=request_params,
                                    headers=headers, verify=False)
            response.raise_for_status()
        except Exception as e:
            raise QueryingError(e)
        else:
            data = response.json()
            if response_location:
                # Get the resources directly from a location in the response
                if isinstance(response_location, str):
                    results = data[response_location]
                elif isinstance(response_location, (list, tuple)):
                    for inner in response_location:
                        data = data[inner]
                    results = data
                return [Resource(**result) for result in results]
            else:
                # Standard response format
                results = data["results"]["bindings"]
                return WebService.build_resources_from_results(results)

    @staticmethod
    def build_resources_from_results(results):
        return [
            Resource(**{k: _process_types(v) for k, v in x.items()})
            for x in results
        ]