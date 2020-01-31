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

from typing import Any, Dict, List, Union

from kgforge.core import Resource
from kgforge.core.conversions.jsonld import as_jsonld


def as_json(data: Union[Resource, List[Resource]], expanded: bool,
            store_metadata: bool) -> Union[Dict, List[Dict]]:
    # FIXME To be refactored after the '@' issue fix. DKE-94.
    # FIXME To be refactored after the implementation of the RDF native conversion. DKE-130.
    def del_context(x: Dict) -> None:
        if "@context" in x:
            del x["@context"]
    if expanded:
        # FIXME Not implemented yet. DKE-130.
        return as_jsonld(data, False, store_metadata)
    else:
        data = as_jsonld(data, True, store_metadata)
        del_context(data) if not isinstance(data, List) else (del_context(x) for x in data)
        # FIXME Hot fix to have DemoStore working before having the proper fix. DKE-130.
        if "@id" in data:
            data["id"] = data.pop("@id")
        if "@type" in data:
            data["type"] = data.pop("@type")
        return data


def from_json(data: Union[Dict, List[Dict]], na: Union[Any, List[Any]]
              ) -> Union[Resource, List[Resource]]:
    nas = na if isinstance(na, List) else [na]
    return _from_json(data, nas)


def _from_json(data: Union[Any, List[Any]], na: List[Any]) -> Any:
    if isinstance(data, List):
        return [_from_json(x, na) for x in data]
    elif isinstance(data, Dict):
        properties = {k: _from_json(v, na) for k, v in data.items() if v not in na}
        return Resource(**properties)
    else:
        return data
