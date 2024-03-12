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

from pyshacl import Shape, validate
import rdflib
from rdflib import OWL, RDF, SH, URIRef, Namespace, Graph
from rdflib.paths import ZeroOrMore, OneOrMore

from kgforge.core.commons.exceptions import RetrievalError
from kgforge.core.commons.rdf_utils import build_shacl_query
from kgforge.core.conversions.rdf import as_jsonld, from_graph
from kgforge.core.archetypes.store import Store
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.service import RdfService, ShapesGraphWrapper
from kgforge.specializations.stores.nexus import Service


class StoreService(RdfService):

    def __init__(
        self,
        default_store: Store,
        context_iri: Optional[str] = None,
        context_store: Optional[Store] = None,
    ) -> None:

        self.default_store = default_store
        self.context_store = context_store or default_store
        # FIXME: define a store independent strategy
        self.store_metadata_iri = (
            self.default_store.service.store_context
            if hasattr(self.default_store.service, "store_context")
            else Namespace(Service.NEXUS_CONTEXT_FALLBACK)
        )
        self._graph = rdflib.Dataset()
        self._sg = ShapesGraphWrapper(self._graph)
        super().__init__(self._graph, context_iri)

    def schema_source_id(self, schema_iri: str) -> str:
        return self.shape_to_defining_resource[schema_iri]

    def materialize(self, iri: URIRef) -> NodeProperties:
        shape = self.get_shape_graph(iri)
        predecessors = set()
        props, attrs = shape.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def _validate(
        self, iri: str, data_graph: Graph, shape: Shape, shacl_graph: Graph
    ) -> Tuple[bool, Graph, str]:
        # _type_shape will make sure all the shapes for this schema are in the graph
        # self._type_shape(iri)
        # schema_graph = self._get_schema_graph(iri)
        return validate(data_graph, shacl_graph=shacl_graph)

    def resolve_context(self, iri: str) -> Dict:
        if iri in self._context_cache:
            return self._context_cache[iri]
        document = self.recursive_resolve(iri)
        self._context_cache.update({iri: document})
        return document

    def generate_context(self) -> Dict:
        for v in self.shape_to_defining_resource.values():
            self.transitive_load_shape_graph(
                self.shape_to_named_graph[v], self.shape_to_defining_resource[v], v
            )
        # reloads the shapes graph
        self._sg = ShapesGraphWrapper(self._graph)
        return self._generate_context()

    def _build_shapes_map(self) -> Tuple[Dict, Dict, Dict]:
        query = build_shacl_query(
            defining_property_uri=self.NXV.shapes,
            deprecated_property_uri=self.NXV.deprecated,
        )
        # consider taking this from the forge config
        limit = 1000
        offset = 0
        count = limit
        class_to_shape = {}
        shape_to_defining_resource = {}
        shape_to_named_graph = {}
        while count == limit:
            resources = self.context_store.sparql(
                query, debug=False, limit=limit, offset=offset
            )
            for r in resources:
                shape_uri = URIRef(r.shape)
                class_to_shape[r.type] = shape_uri
                shape_to_defining_resource[shape_uri] = URIRef(r.resource_id)
                shape_to_named_graph[shape_uri] = URIRef(r.resource_id + "/graph")
            count = len(resources)
            offset += limit
        return class_to_shape, shape_to_defining_resource, shape_to_named_graph

    def recursive_resolve(self, context: Union[Dict, List, str]) -> Dict:
        document = {}
        if isinstance(context, list):
            if self.store_metadata_iri in context:
                context.remove(self.store_metadata_iri)
            if (
                hasattr(self.default_store.service, "store_local_context")
                and self.default_store.service.store_local_context in context
            ):
                context.remove(self.default_store.service.store_local_context)
            for x in context:
                document.update(self.recursive_resolve(x))
        elif isinstance(context, str):
            try:
                local_only = not self.default_store == self.context_store
                doc = self.default_store.service.resolve_context(
                    context, local_only=local_only
                )
            except ValueError:
                try:
                    doc = self.context_store.service.resolve_context(
                        context, local_only=False
                    )
                except ValueError as e:
                    raise e
            document.update(self.recursive_resolve(doc))
        elif isinstance(context, dict):
            document.update(context)
        return document

    def load_shape_graph(self, graph_id, schema_id):
        try:
            schema_resource = self.context_store.retrieve(
                schema_id, version=None, cross_bucket=False
            )
        except RetrievalError as e:
            raise ValueError(f"Failed to retrieve {schema_id}: {str(e)}") from e
        json_dict = as_jsonld(
            schema_resource,
            form="compacted",
            store_metadata=False,
            model_context=None,
            metadata_context=None,
            context_resolver=self.context_store.service.resolve_context,
        )
        # this double conversion was due blank nodes were not "regenerated" with json-ld
        temp_graph = Graph().parse(data=json.dumps(json_dict), format="json-ld")
        schema_graph = self._graph.graph(graph_id)
        schema_graph.parse(data=temp_graph.serialize(format="n3"), format="n3")
        return schema_graph
