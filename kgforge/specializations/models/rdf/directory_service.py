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
import os
from pathlib import Path
from typing import Dict, Tuple

from pyshacl import Shape, validate
import rdflib
from rdflib import OWL, Graph, Namespace, URIRef

from rdflib.util import guess_format

from kgforge.core.commons.context import Context
from kgforge.core.commons.sparql_query_builder import build_shacl_query
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.service import RdfService, ShapesGraphWrapper


class DirectoryService(RdfService):

    def __init__(self, dirpath: Path, context_iri: str) -> None:
        dataset_graph = _load_rdf_files_as_graph(dirpath)
        super().__init__(dataset_graph, context_iri)

    def schema_source_id(self, shape_uri: str) -> str:
        return str(self.shape_to_named_graph[URIRef(shape_uri)])

    def schema_id(self, shape_uri: str) -> str:
        return str(self.shape_to_defining_resource[URIRef(shape_uri)])

    def materialize(self, iri: URIRef) -> NodeProperties:
        sh = self._sg.lookup_shape_from_node(iri)
        predecessors = set()
        props, attrs = sh.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def _validate(
        self, iri: str, data_graph: Graph, shape: Shape, shacl_graph: Graph
    ) -> Tuple[bool, Graph, str]:
        return validate(data_graph, shacl_graph=shacl_graph)

    def resolve_context(self, iri: str) -> Dict:
        if iri in self._context_cache:
            return self._context_cache[iri]

        try:
            context = Context(iri)
        except FileNotFoundError as e:
            raise ValueError(e) from e

        self._context_cache.update({iri: context.document})
        return context.document

    def generate_context(self) -> Dict:
        return self._generate_context()

    def _build_shapes_map(self) -> Tuple[Dict, Dict, Dict, Dict]:
        query = build_shacl_query(
            defining_property_uri=self.NXV.shapes,
            deprecated_property_uri=OWL.deprecated,
            deprecated_optional=True,
            search_in_graph=True,
            context=self.context,
        )
        res = self._graph.query(query)
        class_to_shape = {}
        shape_to_defining_resource = {}
        shape_to_named_graph = {}
        defining_resource_to_named_graph = {}
        for row in res:
            class_to_shape[URIRef(row["type"])] = URIRef(row["shape"])
            shape_to_defining_resource[URIRef(row["shape"])] = URIRef(
                row["resource_id"]
            )
            shape_to_named_graph[URIRef(row["shape"])] = URIRef(row["g"])
            defining_resource_to_named_graph[URIRef(row["resource_id"])] = URIRef(
                row["g"]
            )
        return (
            class_to_shape,
            shape_to_defining_resource,
            shape_to_named_graph,
            defining_resource_to_named_graph,
        )

    def load_shape_graph(self, graph_id: str, schema_id: str) -> Graph:
        return self._graph.graph(rdflib.term.URIRef(graph_id))


def _load_rdf_files_as_graph(path: Path) -> rdflib.Dataset:
    schema_graphs = rdflib.Dataset()
    extensions = [".ttl", ".n3", ".json", ".rdf"]
    for f in path.rglob(os.path.join("*.*")):
        if f.suffix in extensions:
            file_format = guess_format(f.name)
            if file_format is None:
                file_format = "json-ld"
            schema_graph = schema_graphs.graph(rdflib.term.URIRef(f.as_posix()))
            schema_graph.parse(f.as_posix(), format=file_format)
    return schema_graphs
