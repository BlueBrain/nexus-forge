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

from pyshacl import Validator

from kgforge.core import Resource
from kgforge.core.commons.exceptions import RetrievalError
from kgforge.core.conversions.rdf import as_jsonld, as_graph
from rdflib import URIRef, Namespace, Graph

from kgforge.core.archetypes import Store
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.service import RdfService, ShapesGraphWrapper
from kgforge.specializations.stores.nexus import Service


class StoreService(RdfService):

    def __init__(self, default_store: Store, context_iri: Optional[str] = None,
                 context_store: Optional[Store] = None) -> None:

        self.default_store = default_store
        self.context_store = context_store or default_store
        # FIXME: define a store independent strategy
        self.NXV = Namespace(self.default_store.service.namespace) if hasattr(self.default_store.service, "namespace") \
            else Namespace(Service.NEXUS_NAMESPACE_FALLBACK)
        self.store_metadata_iri = self.default_store.service.store_context if hasattr(self.default_store.service, "store_context") \
            else Namespace(Service.NEXUS_CONTEXT_FALLBACK)
        self._shapes_to_resources: Dict
        self._imported = list()
        self._graph = Graph()
        self._sg = ShapesGraphWrapper(self._graph)
        super().__init__(self._graph, context_iri)

    def schema_source_id(self, schema_iri: str) -> str:
        return self._shapes_to_resources[schema_iri]

    def materialize(self, iri: URIRef) -> NodeProperties:
        shape = self._type_shape(iri)
        predecessors = set()
        props, attrs = shape.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def _validate(self, iri: str, data_graph: Graph) -> Tuple[bool, Graph, str]:
        # _type_shape will make sure all the shapes for this type are in the graph
        self._type_shape(iri)
        validator = Validator(data_graph, shacl_graph=self._graph)
        return validator.run()

    def resolve_context(self, iri: str) -> Dict:
        if iri in self._context_cache:
            return self._context_cache[iri]
        document = self.recursive_resolve(iri)
        self._context_cache.update({iri: document})
        return document

    def generate_context(self) -> Dict:
        for v in self._shapes_to_resources.values():
            self._load_shape(v)
        # reloads the shapes graph
        self._sg = ShapesGraphWrapper(self._graph)
        return self._generate_context()

    def _build_shapes_map(self) -> Dict:
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
        class_to_shapes = dict()
        shape_resource = dict()
        while count == limit:
            resources = self.context_store.sparql(query, debug=False, limit=limit, offset=offset)
            for r in resources:
                shape_uri = URIRef(r.shape)
                class_to_shapes[r.type] = shape_uri
                shape_resource[shape_uri] = URIRef(r.resource_id)
            count = len(resources)
            offset += limit
        self._shapes_to_resources = shape_resource
        return class_to_shapes

    def recursive_resolve(self, context: Union[Dict, List, str]) -> Dict:
        document = dict()
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
                local_only = False if self.default_store == self.context_store else True
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

    def _load_shape(self, resource_id):
        if resource_id not in self._imported:
            try:
                shape = self.context_store.retrieve(resource_id, version=None, cross_bucket=False)
            except RetrievalError as e:
                print(e, resource_id)
                # failed, don't try to load again
                self._imported.append(resource_id)
            else:
                json_dict = as_jsonld(shape, form="compacted", store_metadata=False, model_context=None,
                                      metadata_context=None,
                                      context_resolver=self.context_store.service.resolve_context, na=None)
                # this double conversion was due blank nodes were not "regenerated" with json-ld
                temp_graph = Graph().parse(data=json.dumps(json_dict), format="json-ld")
                self._graph.parse(data=temp_graph.serialize(format="n3"), format="n3")
                self._imported.append(resource_id)
                if hasattr(shape, "imports"):
                    for dependency in shape.imports:
                        self._load_shape(self.context.expand(dependency))

    def _type_shape(self, iri: URIRef):
        try:
            shape = self._sg.lookup_shape_from_node(iri)
        except KeyError:
            self._load_shape(self._shapes_to_resources[iri])
            # reloads the shapes graph
            self._sg = ShapesGraphWrapper(self._graph)
            shape = self._sg.lookup_shape_from_node(iri)
        return shape
