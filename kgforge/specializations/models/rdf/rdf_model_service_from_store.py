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
from typing import Dict, Optional, Union, List, Tuple

import json

from pyshacl import validate
from rdflib import URIRef, Namespace, Graph

from kgforge.core.commons.exceptions import RetrievalError
from kgforge.core.conversions.rdf import as_jsonld
from kgforge.core.archetypes.store import Store
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.pyshacl_shape_wrapper import ShapesGraphWrapper, \
    ShapeWrapper
from kgforge.specializations.models.rdf.rdf_model_service import RdfModelService
from kgforge.specializations.stores.nexus import Service


class RdfModelServiceFromStore(RdfModelService):

    def __init__(self, default_store: Store, context_iri: Optional[str] = None,
                 context_store: Optional[Store] = None) -> None:

        self.default_store = default_store
        self.context_store = context_store or default_store
        # FIXME: define a store independent strategy
        self.NXV = Namespace(self.default_store.service.namespace) \
            if hasattr(self.default_store.service, "namespace") \
            else Namespace(Service.NEXUS_NAMESPACE_FALLBACK)

        self.store_metadata_iri = self.default_store.service.store_context \
            if hasattr(self.default_store.service, "store_context") \
            else Namespace(Service.NEXUS_CONTEXT_FALLBACK)

        self._imported = []

        graph, shape_to_resource, class_to_shape = self._build_shapes_map()
        self._shapes_graph = ShapesGraphWrapper(graph)

        super().__init__(
            graph=graph, context_iri=context_iri, shape_to_source=shape_to_resource,
            class_to_shape=class_to_shape
        )

    def materialize(self, iri: URIRef) -> NodeProperties:
        shape: ShapeWrapper = self._load_and_get_type_shape(iri)
        predecessors = set()
        props, attrs = shape.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def _validate(self, iri: str, data_graph: Graph) -> Tuple[bool, Graph, str]:
        # _type_shape will make sure all the shapes for this type are in the graph
        self._load_and_get_type_shape(URIRef(iri))
        return validate(data_graph, shacl_graph=self._graph)

    def resolve_context(self, iri: str) -> Dict:
        if iri not in self._context_cache:
            self._context_cache[iri] = self.recursive_resolve(iri)

        return self._context_cache[iri]

    def generate_context(self) -> Dict:
        for v in self.shape_to_source.values():
            self._load_shape_and_reload_shapes_graph(v)

        return self._generate_context()

    def _build_shapes_map(self) -> Tuple[Graph, Dict[URIRef, str], Dict[str, URIRef]]:
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX sh: <http://www.w3.org/ns/shacl#>
            SELECT ?type ?shape ?resource_id WHERE {{
                {{ ?shape sh:targetClass ?type .
                   ?resource_id <{self.NXV.shapes}> ?shape
                }} UNION {{
                    SELECT (?shape as ?type) ?shape ?resource_id WHERE {{
                        ?shape a sh:NodeShape .
                        ?shape a rdfs:Class .
                        ?resource_id <{self.NXV.shapes}> ?shape
                    }}
                }}
            }} ORDER BY ?type"""

        # make sure to get all types
        limit = 100
        offset = 0
        count = limit
        class_to_shape: Dict[str, URIRef] = dict()
        shape_to_resource: Dict[URIRef, str] = dict()

        while count == limit:
            resources = self.context_store.sparql(query, debug=False, limit=limit, offset=offset)
            for r in resources:
                shape_uri = URIRef(r.shape)
                class_to_shape[r.type] = shape_uri
                shape_to_resource[shape_uri] = URIRef(r.resource_id)
            count = len(resources)
            offset += count

        return Graph(), shape_to_resource, class_to_shape

    def recursive_resolve(self, context: Union[Dict, List, str]) -> Dict:
        document = {}
        if isinstance(context, list):
            if self.store_metadata_iri in context:
                context.remove(self.store_metadata_iri)
            if hasattr(self.default_store.service, "store_local_context") and\
                    self.default_store.service.store_local_context in context:

                context.remove(self.default_store.service.store_local_context)
            for x in context:
                document.update(self.recursive_resolve(x))
        elif isinstance(context, str):

            try:
                local_only = not self.default_store == self.context_store
                doc = self.default_store.service.resolve_context(context, local_only=local_only)
            except ValueError:
                try:
                    doc = self.context_store.service.resolve_context(context, local_only=False)
                except ValueError as e:
                    raise e

            document.update(self.recursive_resolve(doc))
        elif isinstance(context, dict):
            document.update(context)
        return document

    def _load_shape(self, resource_id: str):
        if resource_id not in self._imported:
            try:
                shape = self.context_store.retrieve(resource_id, version=None, cross_bucket=False)
            except RetrievalError as e:
                print(e, resource_id)
                # failed, don't try to load again
                self._imported.append(resource_id)
            else:
                json_dict = as_jsonld(
                    shape, form="compacted", store_metadata=False, model_context=None,
                    metadata_context=None,
                    context_resolver=self.context_store.service.resolve_context
                )
                # this double conversion was due blank nodes were not "regenerated" with json-ld
                temp_graph = Graph().parse(data=json.dumps(json_dict), format="json-ld")
                self._graph.parse(data=temp_graph.serialize(format="n3"), format="n3")
                self._imported.append(resource_id)
                if hasattr(shape, "imports"):
                    for dependency in shape.imports:
                        self._load_shape(self.context.expand(dependency))

    def _load_and_get_type_shape(self, iri: URIRef) -> ShapeWrapper:
        try:
            return self._shapes_graph.lookup_shape_from_node(iri)
        except KeyError:
            shape_resource_id: str = self.shape_to_source[iri]
            self._load_shape_and_reload_shapes_graph(shape_resource_id)
            return self._shapes_graph.lookup_shape_from_node(iri)

    def _load_shape_and_reload_shapes_graph(self, resource_id: str):
        self._load_shape(resource_id)
        # reloads the shapes graph
        self._shapes_graph = ShapesGraphWrapper(self._graph)
