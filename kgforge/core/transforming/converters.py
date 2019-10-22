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
from typing import Dict, List, Tuple, Union, Any

import hjson
from pandas import DataFrame

from kgforge.core.commons.attributes import check_collisions, sort_attributes
from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData, dispatch
from kgforge.core.resources import Resources, Resource, _encode


class Converters:

    # POLICY Converters should be decorated with exceptions.catch() to deal with exceptions.

    @classmethod
    @catch
    def as_json(cls, data: ManagedData, expanded: bool = False,
                store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        def _del_context(x: Dict) -> None:
            del x["@context"]

        if expanded:
            return cls.as_jsonld(data, False, store_metadata)
        else:
            data = cls.as_jsonld(data, True, store_metadata)
            _del_context(data) if not isinstance(data, List) else (_del_context(x) for x in data)
            return data

    @classmethod
    @catch
    def as_jsonld(cls, data: ManagedData, compacted: bool = True,
                  store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        if compacted is False:
            raise NotImplementedError("TODO Implement")
        return dispatch(data, cls._as_jsonld_many, cls._as_jsonld_one, compacted, store_metadata)

    @classmethod
    @catch
    def as_triples(cls, data: ManagedData, store_metadata: bool = False) -> List[Tuple[str, str, str]]:
        # FIXME Implement.
        raise NotImplementedError("TODO Implement")

    @classmethod
    @catch
    def as_dataframe(cls, data: ManagedData, store_metadata: bool = False) -> DataFrame:
        # FIXME Implement.
        raise NotImplementedError("TODO Implement")

    @classmethod
    def _as_jsonld_many(cls, resources: Resources, compacted: bool, store_metadata: bool) -> List[Dict]:
        return [cls._as_jsonld_one(resource, compacted, store_metadata) for resource in resources]

    @classmethod
    def _as_jsonld_one(cls, resource: Resource, compacted: bool, store_metadata: bool) -> Dict:
        # TODO: implement compacted = False

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

        encoded = hjson.loads(hjson.dumps(resource, default=_encode, item_sort_key=sort_attributes))
        context = getattr(resource, "_context", None)
        base = cls.find_in_context(context, "@base")
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

    @classmethod
    def find_in_context(cls, ctx: str, key: str) -> str:
        value = None
        if isinstance(ctx, list):
            for elem in reversed(ctx):
                value = cls.find_in_context(elem, key)
        if value is None:
            if isinstance(ctx, dict):
                if key in ctx:
                    return ctx[key]
        return value