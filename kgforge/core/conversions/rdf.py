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

from copy import deepcopy
from typing import Union, Dict, List, Tuple, Optional, Callable, Any
from urllib.error import URLError, HTTPError

from enum import Enum
from pyld import jsonld
from rdflib import Graph, Literal
import json
from collections import OrderedDict

from rdflib.namespace import RDF
from rdflib_jsonld.keys import CONTEXT, GRAPH, TYPE, ID

from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import NotSupportedError
from kgforge.core.commons.execution import dispatch
from kgforge.core.resource import Resource


class Form(Enum):
    EXPANDED = "expanded"
    COMPACTED = "compacted"


def as_graph(data: Union[Resource, List[Resource]], store_metadata: bool,
             model_context: Optional[Context], metadata_context: Optional[Context],
             context_resolver: Optional[Callable]) -> Graph:
    return dispatch(data, _as_graph_many, _as_graph_one, store_metadata, model_context,
                    metadata_context, context_resolver)


def as_jsonld(data: Union[Resource, List[Resource]], form: str, store_metadata: bool,
              model_context: Optional[Context], metadata_context: Optional[Context],
              context_resolver: Optional[Callable], na: Union[Any, List[Any]]) -> Union[Dict, List[Dict]]:
    try:
        valid_form = Form(form.lower())
    except ValueError:
        supported_forms = tuple(item.value for item in Form)
        raise NotSupportedError(f"supported serialization forms are {supported_forms}")

    return dispatch(
        data, _as_jsonld_many, _as_jsonld_one, valid_form, store_metadata, model_context,
        metadata_context, context_resolver, na)


def from_jsonld(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]:
    if isinstance(data, List) and all(isinstance(x, Dict) for x in data):
        return _from_jsonld_many(data)
    elif isinstance(data, Dict):
        return _from_jsonld_one(data)
    else:
        raise TypeError("not a dictionary nor a list of dictionaries")


def from_graph(data: Graph, type: Optional[Union[str, List]] = None, frame: Dict = None, model_context: Optional[Context] = None) -> Union[Resource, List[Resource]]:

    from collections import OrderedDict


    if not type:
        _types = data.triples((None, RDF.type, None))  # type of data to transform to JSONLD
        _types = [str(_type[2]) for _type in _types]
    else:
        _types = type

    # to get curies as keys when the model context is not used
    graph_n3 = data.serialize(format="n3")
    graph_n3 = Graph().parse(data=graph_n3, format="n3")
    graph_string = graph_n3.serialize(format="json-ld", auto_compact=True, indent=2)
    graph_json = json.loads(graph_string)

    if model_context:
        context =  model_context.document
    else:
        context = graph_json[CONTEXT]

    if not frame:
        frame = {
            "@context": context,
            "@type": _types,
            "@embed": True
        }

    framed = jsonld.frame(graph_json, frame)
    framed = _graph_free_jsonld(framed)
    if isinstance(framed, list):
        framed = [jsonld.compact(item, ctx=context,
                                options={'processingMode': 'json-ld-1.1'}) for item in framed]
    else:
        framed = jsonld.compact(framed, ctx=context,
                                options={'processingMode': 'json-ld-1.1'})
    return from_jsonld(framed)


def _graph_free_jsonld(jsonld_doc, context=None):
    results = []
    if GRAPH in jsonld_doc and len(jsonld_doc[GRAPH]) > 0:
        for graph_free_jsonld_doc in jsonld_doc[GRAPH]:
            if not context and CONTEXT in jsonld_doc:
                context = jsonld_doc[CONTEXT]

            graph_free = OrderedDict(graph_free_jsonld_doc)
            if context:
                graph_free[CONTEXT] = context
                graph_free.move_to_end(CONTEXT, last=False)
            results.append(graph_free)
        return results
    else:
        return jsonld_doc


def _from_jsonld_many(dataset: List[Dict]) -> List[Resource]:
    return [_from_jsonld_one(data) for data in dataset]


def _from_jsonld_one(data: Dict) -> Resource:
    if "@context" in data:
        try:
            resolved_context = Context(data["@context"])
        except URLError:
            raise ValueError("context not resolvable")
        else:
            return _remove_ld_keys(data, resolved_context)
    else:
        raise NotImplementedError("not implemented yet (expanded json-ld)")


def _as_jsonld_many(resources: List[Resource], form: Form, store_metadata: bool,
                    model_context: Optional[Context], metadata_context: Optional[Context],
                    context_resolver: Optional[Callable], na: Optional[List[Any]]) -> List[Dict]:
    if na is not None and len(na) != len(resources):
        raise ValueError(f"len(na) should be equal to len(resources): {len(na)} != {len(resources)}")

    return [_as_jsonld_one(resource, form, store_metadata, model_context, metadata_context,
                           context_resolver, na[i]) if na is not None else
            _as_jsonld_one(resource, form, store_metadata, model_context, metadata_context,
                           context_resolver, na)
            for i, resource in enumerate (resources)]


def _as_jsonld_one(resource: Resource, form: Form, store_metadata: bool,
                   model_context: Optional[Context], metadata_context: Optional[Context],
                   context_resolver: Optional[Callable], na: Any) -> Dict:
    context = _resource_context(resource, model_context, context_resolver)
    resolved_context = context.document
    output_context = context.iri if context.is_http_iri() else context.document["@context"]
    resource_types = getattr(resource, "type", getattr(resource, "@type", None))
    # this is to ensure the framing is centered on the provided resource in case nested resources share the same type
    resource.type = "https://bluebrain.github.io/nexus/vocabulary/FramedType"
    if store_metadata and resource._store_metadata:
        if metadata_context:
            resolved_context = _merge_jsonld(resolved_context["@context"],
                                             metadata_context.document["@context"])
            if metadata_context.is_http_iri():
                metadata_context_output = metadata_context.iri
            else:
                metadata_context_output = metadata_context.document["@context"]
            output_context = _merge_jsonld(output_context, metadata_context_output)
        else:
            raise NotSupportedError("no available context in the metadata")
    try:
        data_graph, metadata_graph, encoded_resource = _as_graphs(resource, store_metadata, context, metadata_context)
        data_graph.remove((None, None, Literal(na)))
    except Exception as e:
        raise ValueError(e)
    jsonld_data_expanded = jsonld.expand(encoded_resource, options={'expandContext': resolved_context})

    if hasattr(resource, "id") or hasattr(resource, "@id"):
        if context.base:
            uri = context.resolve(resource.id)
        else:
            uri = str(data_graph.namespace_manager.absolutize(resource.id, defrag=0)) if not str(resource.id).startswith("_:") else resource.id
        frame = {"@id": uri}
    else:
        frame = dict()
        for k, v in resource.__dict__.items():
            if k not in Resource._RESERVED and not isinstance(v, (Resource, dict, list)):
                if k == "context":
                    continue
                elif k == "type" or k == TYPE:
                    t = context.expand(v)
                    if t:
                        frame["@type"] = context.expand(v)
                else:
                    key = context.expand(k)
                    if key and isinstance(v, str):
                        frame[key] = v
    frame["@embed"] = "@link"
    data_framed = jsonld.frame(jsonld_data_expanded, frame, options={'processingMode': 'json-ld-1.1'})
    resource_graph_node = _graph_free_jsonld(data_framed)
    if resource_types is None:
        resource_graph_node.pop(TYPE)
    else:
        resource_graph_node[TYPE] = context.expand(resource_types) if isinstance(resource_types, str) else [context.expand(resource_type) for resource_type in resource_types]
    resource.type = resource_types
    if store_metadata is True and len(metadata_graph) > 0:
        metadata_expanded = json.loads(metadata_graph.serialize(format="json-ld").decode("utf-8"))
        metadata_framed = jsonld.frame(metadata_expanded, {"@id": resource.id})
        if form is Form.COMPACTED:
            data_compacted = jsonld.compact(data_framed, resolved_context)
            metadata_compacted = jsonld.compact(metadata_framed, resolved_context)
            metadata_compacted = dict(sorted(metadata_compacted.items()))
            data_and_meta = _merge_jsonld(data_compacted, metadata_compacted)
            data_and_meta["@context"] = output_context
            # this is to be able to register contexts documents
            if len(data_compacted) == 1 and hasattr(resource, "id"):
                data_compacted["@id"] = resource.id
            return data_and_meta
        elif form is Form.EXPANDED:
            data_expanded = _unpack_from_list(data_framed)

            metadata_expanded = _unpack_from_list(metadata_framed)
            metadata_expanded = dict(sorted(metadata_expanded.items()))
            return _merge_jsonld(data_expanded, metadata_expanded)
    else:
        if form is Form.COMPACTED:
            compacted = jsonld.compact(data_framed, resolved_context)
            compacted["@context"] = output_context
            # this is to be able to register contexts documents
            if len(compacted) == 1 and hasattr(resource, "id"):
                compacted["@id"] = resource.id
            return compacted
        elif form is Form.EXPANDED:
            return _unpack_from_list(data_framed)

def _as_graph_many(resources: List[Resource], store_metadata: bool, model_context: Optional[Context],
                   metadata_context: Optional[Context], context_resolver: Optional[Callable]) -> Graph:
    graph = Graph()
    for resource in resources:
        # Do not use _as_graph_one as it will lead to using graph1 + graph2 operation which can lead to blank node collisions
        json_ld = _as_jsonld_one(resource, Form.EXPANDED, store_metadata, model_context,
                                 metadata_context, context_resolver, None)
        graph.parse(data=json.dumps(json_ld), format="json-ld")
    return graph


def _as_graph_one(resource: Resource, store_metadata: bool, model_context: Optional[Context],
                  metadata_context: Optional[Context], context_resolver: Optional[Callable]) -> Graph:
    json_ld = _as_jsonld_one(resource, Form.EXPANDED, store_metadata, model_context,
                             metadata_context, context_resolver, None)
    return Graph().parse(data=json.dumps(json_ld), format="json-ld")


def _as_graphs(resource: Resource, store_metadata: bool, context: Context,
               metadata_context: Context) -> Tuple[Graph, Graph, Dict]:
    """Returns a data and a metadata graph"""
    if hasattr(resource, "context"):
        output_context = resource.context
    else:
        output_context = context.iri if context.is_http_iri() else context.document["@context"]
    converted = _add_ld_keys(resource, output_context, context.base)
    converted["@context"] = context.document["@context"]
    return _dicts_to_graph(converted, resource._store_metadata, store_metadata, metadata_context)+ (converted,)


def _dicts_to_graph(data: Dict, metadata: Dict, store_meta: bool,
                    metadata_context: Context) -> Tuple[Graph, Graph]:
    json_str = json.dumps(data)
    graph = Graph().parse(data=json_str, format="json-ld")
    meta_data_graph = Graph()
    if store_meta is True and metadata is not None:
        if "id" not in metadata:
            raise ValueError("no id in the metadata")
        metadata = _add_ld_keys(metadata, None, None)
        metadata["@context"] = metadata_context.document["@context"]
        try:
            meta_data_graph.parse(data=json.dumps(metadata), format="json-ld")
        except Exception:
            raise ValueError("generated an invalid json-ld")
    return graph, meta_data_graph


def recursive_resolve(context: Union[Dict, List, str], resolver: Optional[Callable]) -> Dict:
    document = dict()
    if isinstance(context, list):
        for x in context:
            document.update(recursive_resolve(x, resolver))
    elif isinstance(context, str):
        doc = resolver(context)
        document.update(recursive_resolve(doc, resolver))
    elif isinstance(context, dict):
        document.update(context)
    return document


def _resource_context(resource: Resource, model_context: Context, context_resolver: Callable) -> Context:
    if hasattr(resource, "context"):
        if model_context and resource.context == model_context.iri:
            context = model_context
        else:
            iri = resource.context if isinstance(resource.context, str) else None
            try:
                document = recursive_resolve(resource.context, context_resolver)
                context = Context(document, iri)
            except (HTTPError, URLError, NotSupportedError):
                try:
                    context = Context(resource.context, iri)
                except URLError:
                    raise ValueError(f"{resource.context} is not resolvable")
    else:
        context = model_context

    if context is None:
        raise NotSupportedError("no available context")

    return context


def _unpack_from_list(data):
    if isinstance(data, list):
        node = data
    elif isinstance(data, dict):
        if "@graph" in data:
            node = data["@graph"]
        else:
            return data
    else:
        return data
    if len(node) == 1:
        return node[0]
    else:
        return node


def _dicts_to_graph(data: Dict, metadata: Dict, store_meta: bool,
                    metadata_context: Context) -> Tuple[Graph, Graph]:
    json_str = json.dumps(data)
    graph = Graph().parse(data=json_str, format="json-ld")
    meta_data_graph = Graph()
    if store_meta is True and metadata is not None:
        if "id" not in metadata:
            raise ValueError("no id in the metadata")
        metadata = _add_ld_keys(metadata, None, None)
        metadata["@context"] = metadata_context.document["@context"]
        try:
            meta_data_graph.parse(data=json.dumps(metadata), format="json-ld")
        except Exception:
            raise ValueError("generated an invalid json-ld")
    return graph, meta_data_graph


def _add_ld_keys(rsc: [Resource, Dict], context: Optional[Union[Dict, List, str]], base: Optional[str]) -> Dict:
    local_attrs = dict()
    ld_keys = {"id": "@id", "type": "@type", "list": "@list", "set": "@set"}
    local_context = None
    items = rsc.__dict__.items() if isinstance(rsc, Resource) else rsc.items()
    for k, v in items:
        if k not in Resource._RESERVED:
            if k == "context":
                if v != context:
                    local_context = Context(v)
                    base = local_context.base
            else:
                key = ld_keys.get(k, k)
                if key == "@id" and local_context is not None:
                    local_attrs[key] = local_context.resolve(v)
                else:
                    if isinstance(v, Resource) or isinstance(v, Dict):
                        local_attrs[key] = _add_ld_keys(v, context, base)
                    elif isinstance(v, list):
                        local_attrs[key] = [_add_ld_keys(item, context, base)
                                            if isinstance(item, Resource) or isinstance(item, Dict)
                                            else item for item in v]
                    else:
                        if isinstance(v, LazyAction):
                            raise ValueError("can't convert, resource contains LazyActions")
                        local_attrs[key] = v.replace(base, "") if base and isinstance(v, str) else v
    return local_attrs


def _remove_ld_keys(dictionary: dict, context: Context,
                    to_resource: Optional[bool] = True) -> Union[Dict, Resource]:
    local_attrs = dict()
    for k, v in dictionary.items():
        if k == "@context":
            if v != context:
                local_attrs["context"] = v
        else:
            if k == "@id":
                local_attrs["id"] = context.resolve(v)
            elif k.startswith("@"):
                local_attrs[k[1:]] = v
            else:
                if isinstance(v, dict):
                    local_attrs[k] = _remove_ld_keys(v, context, to_resource)
                elif isinstance(v, list):
                    local_attrs[k] = [_remove_ld_keys(item, context, to_resource)
                                      if isinstance(item, dict) else item for item in v]
                else:
                    if k in context.terms:
                        if context.terms[k].type == "@id":
                            v = context.shrink_iri(v)
                    local_attrs[k] = v
    if to_resource:
        return Resource(**local_attrs)
    else:
        return local_attrs


# Context


def _merge_dict_into_list(list_: List, dictionary: Dict) -> List:
    merged = False
    for item in list_:
        if isinstance(item, dict):
            item.update(dictionary)
            merged = True
            break
    if not merged:
        list_.append(dictionary)


def _merge_str_into_list(list_: List, string: str) -> List:
    if string not in list_:
        list_.append(string)


def _merge_second_list_into_first(first: List, second: List) -> List:
    for element in second:
        if isinstance(element, str):
            _merge_str_into_list(first, element)
        elif isinstance(element, dict):
            _merge_dict_into_list(first, element)


def _merge_jsonld(first: Union[Dict, List, str], second: Union[Dict, List, str]) -> Union[Dict, List, str]:
    result = None
    if isinstance(first, str):
        if isinstance(second, str):
            if first != second:
                result = [first, second]
            else:
                result = first
        elif isinstance(second, dict):
            result = [first, second]
        elif isinstance(second, list):
            result = [first]
            for element in second:
                if element != first:
                    result.append(element)
    if isinstance(first, list):
        result = deepcopy(first)
        if isinstance(second, str):
            _merge_str_into_list(result, second)
        if isinstance(second, dict):
            _merge_dict_into_list(result, second)
        if isinstance(second, list):
            _merge_second_list_into_first(result, second)
    if isinstance(first, dict):
        if isinstance(second, str):
            result = [deepcopy(first), deepcopy(second)]
        elif isinstance(second, dict):
            result = deepcopy(first)
            result.update(second)
        elif isinstance(second, list):
            result = [deepcopy(first)]
            _merge_second_list_into_first(result, second)
    return result
