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

import os
import json
import requests
from typing import Optional, Any

from kgforge.core import Resource
from kgforge.core.commons.exceptions import DownloadingError, QueryingError


def type_from_filters(*filters) -> Optional[str]:
    """Returns the first `type` found in filters."""
    resource_type = None
    filters = filters[0]
    if isinstance(filters, dict):
        if 'type' in filters:
            resource_type = filters['type']
    else:
        # check filters grouping
        if isinstance(filters, (list, tuple)):
            filters = [filter for filter in filters]
        else:
            filters = [filters]
        for filter in filters:
            if 'type' in filter.path and filter.operator is "__eq__":
                resource_type = filter.value
                break
    return resource_type

def resources_from_results(results):
    """Returns Resources from standard response bindings."""
    return [
        Resource(**{k: json.loads(str(v["value"]).lower()) if v['type'] =='literal' and
                                                              ('datatype' in v and v['datatype']=='http://www.w3.org/2001/XMLSchema#boolean')
                                                           else (int(v["value"]) if v['type'] =='literal' and
                                                                 ('datatype' in v and v['datatype']=='http://www.w3.org/2001/XMLSchema#integer')
                                                                 else v["value"]
                                                                 )
                    for k, v in x.items()} )
        for x in results
    ]

def resources_from_request(url, headers, **params):
    """Perform a HTTP request
    params:
    -------
        response_loc : list[str]
            The nested location of the relevat metadata in the
            response.
            Example: NeuroMorpho uses response["_embedded"]["neuronResources"]
            which should be given as: response_loc = ["_embedded", "neuronResources"]
    """
    response_location = params.pop('response_loc', None)
    try:
        response = requests.get(
            url, params=params, headers=headers, verify=False
        )
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
            return resources_from_results(results)