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

from rdflib.plugins.shared.jsonld.keys import CONTEXT, TYPE, GRAPH
from typing import Union, Dict, List, Tuple, Optional, Callable, Any
from urllib.error import URLError, HTTPError

from enum import Enum
from pyld import jsonld
from rdflib import Graph, Literal
import json
from collections import OrderedDict
from rdflib.namespace import RDF

from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import NotSupportedError
from kgforge.core.commons.execution import dispatch
from kgforge.core.resource import Resource


class Form(Enum):
    EXPANDED = "expanded"
    COMPACTED = "compacted"


LD_KEYS = {"id": "@id", "type": "@type", "list": "@list", "set": "@set"}


def as_graph(
    data: Union[Resource, List[Resource]],
    store_metadata: bool,
    model_context: Optional[Context],
    metadata_context: Optional[Context],
    context_resolver: Optional[Callable],
) -> Graph:
    return dispatch(
        data,
        _as_graph_many,
        _as_graph_one,
        store_metadata,
        model_context,
        metadata_context,
        context_resolver,
    )


def as_jsonld(
    data: Union[Resource, List[Resource]],
    form: str,
    store_metadata: bool,
    model_context: Optional[Context],
    metadata_context: Optional[Context],
    context_resolver: Optional[Callable],
    **params
) -> Union[Dict, List[Dict]]:
    try:
        valid_form = Form(form.lower())
    except ValueError:
        supported_forms = tuple(item.value for item in Form)
        raise NotSupportedError(f"supported serialization forms are {supported_forms}")

    return dispatch(
        data,
        _as_jsonld_many,
        _as_jsonld_one,
        valid_form,
        store_metadata,
        model_context,
        metadata_context,
        context_resolver,
        **params
    )


def from_jsonld(data: Union[Dict, List[Dict]]) -> Union[Resource, List[Resource]]:
    if isinstance(data, List) and all(isinstance(x, Dict) for x in data):
        return _from_jsonld_many(data)
    elif isinstance(data, Dict):
        return _from_jsonld_one(data)
    else:
        raise TypeError("not a dictionary nor a list of dictionaries")


def from_graph(
    data: Graph,
    type: Optional[Union[str, List]] = None,
    frame: Dict = None,
    model_context: Optional[Context] = None,
) -> Union[Resource, List[Resource]]:
    from collections import OrderedDict

    if not type:
        _types = data.triples(
            (None, RDF.type, None)
        )  # type of data to transform to JSONLD
        _types = [str(_type[2]) for _type in _types]
    else:
        _types = type

    # to get curies as keys when the model context is not used
    graph_n3 = data.serialize(format="n3")
    graph_n3 = Graph().parse(data=graph_n3, format="n3")
    graph_string = graph_n3.serialize(format="json-ld", auto_compact=True, indent=2)
    graph_json = json.loads(graph_string)

    if model_context:
        context = model_context.document
    else:
        context = graph_json[CONTEXT]

    if not frame:
        frame = {"@context": context, "@type": _types, "@embed": True}

    framed = jsonld.frame(graph_json, frame)
    framed = _graph_free_jsonld(framed)
    if isinstance(framed, list):
        framed = [
            jsonld.compact(item, ctx=context, options={"processingMode": "json-ld-1.1"})
            for item in framed
        ]
    else:
        framed = jsonld.compact(
            framed, ctx=context, options={"processingMode": "json-ld-1.1"}
        )
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


def _as_jsonld_many(
    resources: List[Resource],
    form: Form,
    store_metadata: bool,
    model_context: Optional[Context],
    metadata_context: Optional[Context],
    context_resolver: Optional[Callable],
    **params
) -> List[Dict]:
    return [
         _as_jsonld_one(
            resource,
            form,
            store_metadata,
            model_context,
            metadata_context,
            context_resolver,
            **params) for i, resource in enumerate(resources)
    ]


def _as_jsonld_one(
    resource: Resource,
    form: Form,
    store_metadata: bool,
    model_context: Optional[Context],
    metadata_context: Optional[Context],
    context_resolver: Optional[Callable],
    **params
) -> Dict:
    context = _resource_context(resource, model_context, context_resolver)
    resolved_context = deepcopy(context.document)
    output_context = (
        context.iri if context.is_http_iri() else context.document["@context"]
    )
    if store_metadata and resource._store_metadata:
        if metadata_context:
            resolved_context = _merge_jsonld(
                resolved_context["@context"], metadata_context.document["@context"]
            )
            if metadata_context.is_http_iri():
                metadata_context_output = metadata_context.iri
            else:
                metadata_context_output = metadata_context.document["@context"]
            output_context = _merge_jsonld(output_context, metadata_context_output)
        else:
            raise NotSupportedError("no available context in the metadata")
    try:
        data_graph, metadata_graph, encoded_resource, json_array = _as_graphs(
            resource, store_metadata, context, metadata_context
        )
    except Exception as e:
        raise ValueError(e)

    if store_metadata is True and len(metadata_graph) > 0:
        metadata_expanded = json.loads(metadata_graph.serialize(format="json-ld"))
        if form is Form.COMPACTED:
            metadata_compacted = jsonld.compact(metadata_expanded, resolved_context)
            metadata_update = dict(sorted(metadata_compacted.items()))
            result = encoded_resource
        elif form is Form.EXPANDED:
            jsonld_data_expanded = jsonld.expand(
                encoded_resource, options={"expandContext": resolved_context}
            )
            jsonld_data_expanded = _unpack_from_list(jsonld_data_expanded)
            metadata_expanded = _unpack_from_list(metadata_expanded)
            metadata_update = dict(sorted(metadata_expanded.items()))
            result = jsonld_data_expanded
        result.update(metadata_update)
    else:
        if form is Form.COMPACTED:
            result = encoded_resource
        elif form is Form.EXPANDED:
            jsonld_data_expanded = jsonld.expand(
                encoded_resource, options={"expandContext": resolved_context}
            )
            result = _unpack_from_list(jsonld_data_expanded)
    if isinstance(result, dict):
        if "@context" in result:
            result.pop("@context")
        result = {**{"@context": output_context}, **result} if form is Form.COMPACTED else result
        resource_id = resource.id if hasattr(resource, "id") else (getattr(resource, "@id") if hasattr(resource, "@id") else None)
        if resource_id:
            result["@id"] = resource_id
    else:
        raise ValueError("Unable to convert to JSON-LD")
    return result


def _as_graph_many(
    resources: List[Resource],
    store_metadata: bool,
    model_context: Optional[Context],
    metadata_context: Optional[Context],
    context_resolver: Optional[Callable],
) -> Graph:
    graph = Graph()
    for resource in resources:
        # Do not use _as_graph_one as it will lead to using graph1 + graph2 operation which can lead to blank node collisions
        json_ld = _as_jsonld_one(
            resource,
            Form.EXPANDED,
            store_metadata,
            model_context,
            metadata_context,
            context_resolver
        )
        graph.parse(data=json.dumps(json_ld), format="json-ld")
    return graph


def _as_graph_one(
    resource: Resource,
    store_metadata: bool,
    model_context: Optional[Context],
    metadata_context: Optional[Context],
    context_resolver: Optional[Callable],
) -> Graph:
    json_ld = _as_jsonld_one(
        resource,
        Form.EXPANDED,
        store_metadata,
        model_context,
        metadata_context,
        context_resolver
    )
    return Graph().parse(data=json.dumps(json_ld), format="json-ld")


def _as_graphs(
    resource: Resource,
    store_metadata: bool,
    context: Context,
    metadata_context: Context,
) -> Tuple[Graph, Graph, Dict, List[str]]:
    """Returns a data and a metadata graph"""
    if hasattr(resource, "context"):
        output_context = resource.context
    else:
        output_context = (
            context.iri if context.is_http_iri() else context.document["@context"]
        )
    converted, json_array = _add_ld_keys(resource, output_context, context.base)
    converted["@context"] = context.document["@context"]
    return _dicts_to_graph(converted, resource._store_metadata, store_metadata, metadata_context)+(converted, ) + (json_array, )


def _dicts_to_graph(
    data: Dict, metadata: Dict, store_meta: bool, metadata_context: Context
) -> Tuple[Graph, Graph]:
    json_str = json.dumps(data)
    graph = Graph().parse(data=json_str, format="json-ld")
    meta_data_graph = Graph()
    if store_meta is True and metadata is not None:
        if "id" not in metadata:
            raise ValueError("no id in the metadata")
        metadata, _ = _add_ld_keys(metadata, None, None)
        metadata["@context"] = metadata_context.document["@context"]
        try:
            meta_data_graph.parse(data=json.dumps(metadata), format="json-ld")
        except Exception:
            raise ValueError("generated an invalid json-ld")
    return graph, meta_data_graph


def recursive_resolve(
    context: Union[Dict, List, str],
    resolver: Optional[Callable],
    already_loaded: List = [],
) -> Dict:
    document = dict()
    if isinstance(context, list):
        for x in context:
            if x not in already_loaded:
                document.update(recursive_resolve(x, resolver, already_loaded))
    elif isinstance(context, str) and context not in already_loaded:
        doc = resolver(context)
        document.update(recursive_resolve(doc, resolver, already_loaded))
        already_loaded.append(context)
    elif isinstance(context, dict):
        document.update(context)
    return document


def _resource_context(
    resource: Resource, model_context: Context, context_resolver: Callable
) -> Context:
    if hasattr(resource, "context"):
        if model_context and resource.context == model_context.iri:
            context = model_context
        else:
            iri = resource.context if isinstance(resource.context, str) else None
            try:
                document = recursive_resolve(
                    resource.context,
                    context_resolver,
                    [
                        "https://bluebrainnexus.io/contexts/metadata.json",
                        "https://bluebrain.github.io/nexus/contexts/metadata.json",
                    ],
                )
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


def _add_ld_keys(
    rsc: [Resource, Dict],
    context: Optional[Union[Dict, List, str]],
    base: Optional[str],
) -> Union[Dict, List[str]]:
    local_attrs = dict()
    local_context = None
    json_arrays = []
    items = rsc.__dict__.items() if isinstance(rsc, Resource) else rsc.items()
    for k, v in items:
        if k not in Resource._RESERVED:
            if k == "context":
                if v != context:
                    local_context = Context(v)
                    base = local_context.base
            else:
                key = LD_KEYS.get(k, k)
                if key == "@id" and local_context is not None:
                    local_attrs[key] = local_context.resolve(v)
                else:

                    if isinstance(v, Resource) or isinstance(v, Dict):
                        attrs = _add_ld_keys(v, context, base)
                        local_attrs[key] = attrs[0]
                        json_arrays.extend(attrs[1])
                    elif isinstance(v, list):

                        l_a = []
                        j_a = []
                        for item in v:
                            if isinstance(item, Resource) or isinstance(item, Dict):
                                attrs = _add_ld_keys(item, context, base)
                                l_a.append(attrs[0])
                                j_a.extend(attrs[1])
                            else:
                                l_a.append(item)
                        local_attrs[key] = l_a
                        json_arrays.append(k)
                        json_arrays.extend(j_a)

                    else:
                        if isinstance(v, LazyAction):
                            raise ValueError(
                                "can't convert, resource contains LazyActions"
                            )
                        local_attrs[key] = (
                            v.replace(base, "") if base and isinstance(v, str) else v
                        )
    return local_attrs, json_arrays


def _remove_ld_keys(
    dictionary: dict, context: Context, to_resource: Optional[bool] = True
) -> Union[Dict, Resource]:
    local_attrs = dict()
    for k, v in dictionary.items():
        if k == "@context":
            if v != context:
                local_attrs["context"] = v
        else:
            if k == "@id":
                local_attrs["id"] = context.resolve(v)
            elif k.startswith("@") and k in LD_KEYS.values():
                local_attrs[k[1:]] = v
            else:
                if isinstance(v, dict):
                    local_attrs[k] = _remove_ld_keys(v, context, to_resource)
                elif isinstance(v, list):
                    local_attrs[k] = [
                        _remove_ld_keys(item, context, to_resource)
                        if isinstance(item, dict)
                        else item
                        for item in v
                    ]
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


def _merge_jsonld(
    first: Union[Dict, List, str], second: Union[Dict, List, str]
) -> Union[Dict, List, str]:
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
