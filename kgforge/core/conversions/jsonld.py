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

from collections import OrderedDict
from typing import Any, Dict, List, Tuple, Union

import hjson

from kgforge.core.commons.attributes import check_collisions, sort_attrs
from kgforge.core.commons.execution import catch, dispatch
from kgforge.core.resource import Resource, encode


# FIXME To be re-implemented with a RDF native solution. DKE-130.


@catch
def as_jsonld(data: Union[Resource, List[Resource]], compacted: bool,
              store_metadata: bool) -> Union[Dict, List[Dict]]:
    if compacted is False:
        raise NotImplementedError("not implemented yet")
    return dispatch(data, _as_jsonld_many, _as_jsonld_one, compacted, store_metadata)


@catch
def from_jsonld(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]:
    raise NotImplementedError("not implemented yet")


def _as_jsonld_many(resources: List[Resource], compacted: bool,
                    store_metadata: bool) -> List[Dict]:
    return [_as_jsonld_one(resource, compacted, store_metadata) for resource in resources]


def _as_jsonld_one(resource: Resource, compacted: bool, store_metadata: bool) -> Dict:
    # TODO: Implement compacted = False. DKE-130.
    encoded = hjson.loads(hjson.dumps(resource, default=encode, item_sort_key=sort_attrs))
    context = getattr(resource, "_context", None)
    base = find_in_context(context, "@base")
    converted = convert(encoded, base)
    # TODO: handle where nested resources have different contexts, then, context has to be merged first
    if context is not None:
        converted["@context"] = context
        converted.move_to_end("@context", last=False)
    if store_metadata:
        metadata = resource._store_metadata
        if metadata is not None:
            check_collisions(set(converted.keys()), metadata.keys())
            converted.update(metadata)
    return converted


def prepare(k: str, v: Any, ctx_base: str) -> Tuple[str, Any]:
    ld_keys = {"id": "@id", "type": "@type"}
    if k in ld_keys:
        value = v.replace(ctx_base, "") if ctx_base else v
        return ld_keys[k], value
    elif isinstance(v, dict):
        return k, convert(v, ctx_base)
    elif isinstance(v, list):
        value = [convert(item, ctx_base) if isinstance(item, dict) else item for item in v]
        return k, value
    else:
        return k, v


def convert(data: Dict, ctx_base: str) -> OrderedDict:
    return OrderedDict(prepare(k, v, ctx_base) for k, v in data.items())


def find_in_context(ctx: str, key: str) -> str:
    value = None
    if isinstance(ctx, list):
        for elem in reversed(ctx):
            value = find_in_context(elem, key)
    if value is None:
        if isinstance(ctx, dict):
            if key in ctx:
                return ctx[key]
    return value
