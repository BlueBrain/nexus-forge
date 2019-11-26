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
from kgforge.core.commons.execution import catch
from kgforge.core.conversions.jsonld import as_jsonld


@catch
def as_json(data: Union[Resource, List[Resource]], expanded: bool,
            store_metadata: bool) -> Union[Dict, List[Dict]]:
    # FIXME To be refactored after the '@' issue fix.
    # FIXME To be refactored after the implementation of the RDF native conversion.
    def del_context(x: Dict) -> None:
        if "@context" in x:
            del x["@context"]
    if expanded:
        # FIXME Not implemented yet.
        return as_jsonld(data, False, store_metadata)
    else:
        data = as_jsonld(data, True, store_metadata)
        del_context(data) if not isinstance(data, List) else (del_context(x) for x in data)
        # FIXME Hot fix to have DemoStore working before having the proper fix.
        if "@id" in data:
            data["id"] = data.pop("@id")
        if "@type" in data:
            data["type"] = data.pop("@type")
        return data


@catch
def from_json(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]:
    if isinstance(data, List) and all(isinstance(x, Dict) for x in data):
        return [from_json(x) for x in data]
    elif isinstance(data, Dict):
        properties = {k: _from_json(v) for k, v in data.items()}
        return Resource(**properties)
    else:
        raise TypeError("not a Dict nor a list of Dict")


def _from_json(value: Any) -> Any:
    if isinstance(value, List):
        return [_from_json(x) for x in value]
    elif isinstance(value, Dict):
        return from_json(value)
    else:
        return value
