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

import json
from typing import Any, Dict, List, Union, Optional, Callable

import hjson

from kgforge.core import Resource
from kgforge.core.commons.attributes import sort_attrs
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import as_jsonld
from kgforge.core.resource import encode


def as_json(data: Union[Resource, List[Resource]], expanded: bool, store_metadata: bool,
            model_context: Optional[Context], metadata_context: Optional[Context],
            context_resolver: Optional[Callable]) -> Union[Dict, List[Dict]]:
    if expanded:
        return as_jsonld(data, "expanded", store_metadata, model_context=model_context,
                         metadata_context=metadata_context, context_resolver=context_resolver, na=None)
    else:
        if isinstance(data, Resource):
            return _as_json(data, store_metadata)
        else:
            return [_as_json(x, store_metadata) for x in data]


def from_json(data: Union[Dict, List[Dict]], na: Union[Any, List[Any]]
              ) -> Union[Resource, List[Resource]]:
    return Resource.from_json(data, na)


def _as_json(resource: Resource, store_metadata: bool) -> Dict:
    data = json.loads(hjson.dumpsJSON(resource, default=encode, item_sort_key=sort_attrs))
    _remove_context(data)
    if store_metadata is True and resource._store_metadata:
        data.update(json.loads(hjson.dumpsJSON(resource._store_metadata, item_sort_key=sort_attrs)))
    return data


def _remove_context(dictionary: dict):
    if isinstance(dictionary, dict):
        for i in list(dictionary):
            if i == "context":
                dictionary.pop("context")
            else:
                if isinstance(dictionary[i], dict):
                    _remove_context(dictionary[i])
                elif isinstance(dictionary[i], list):
                    for x in dictionary[i]:
                        _remove_context(x)

