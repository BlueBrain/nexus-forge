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

from pyshacl import validate
from rdflib import Graph, URIRef
from rdflib.util import guess_format

from kgforge.core.commons.context import Context
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.rdf_model_service import RdfModelService


class RdfModelServiceFromDirectory(RdfModelService):

    def __init__(self, dir_path: Path, context_iri: str) -> None:
        self.dir_path = dir_path
        super().__init__(context_iri=context_iri)

    def materialize(self, iri: URIRef) -> NodeProperties:
        sh = self._shapes_graph.lookup_shape_from_node(iri)
        predecessors = set()
        props, attrs = sh.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def _validate(self, iri: str, data_graph: Graph) -> Tuple[bool, Graph, str]:
        return validate(data_graph, shacl_graph=self._graph)

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

    def _build_shapes_map(self) -> Tuple[Graph, Dict[URIRef, str], Dict[str, URIRef]]:

        query = """
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX sh: <http://www.w3.org/ns/shacl#>
                    SELECT ?type ?shape WHERE {
                        { ?shape sh:targetClass ?type .}
                        UNION {
                            SELECT (?shape as ?type) ?shape WHERE {
                                ?shape a sh:NodeShape .
                                ?shape a rdfs:Class
                            }
                        }
                    } ORDER BY ?type
                """

        class_to_shape: Dict[str, URIRef] = dict()
        shape_to_file: Dict[URIRef, str] = dict()
        graph = Graph()

        extensions = [".ttl", ".n3", ".json", ".rdf"]
        for f in self.dir_path.rglob(os.path.join("*.*")):
            graph_i = Graph()
            if f.suffix in extensions:
                file_format = guess_format(f.name)
                if file_format is None:
                    file_format = "json-ld"
                graph_i.parse(f.as_posix(), format=file_format)

            res = graph_i.query(query)

            class_to_shape_i = dict(
                (row["type"], URIRef(row["shape"]))
                for row in res
            )
            class_to_shape.update(class_to_shape_i)

            shape_to_file.update(dict(
                (e, f.as_posix())
                for e in class_to_shape_i.values()
            ))

            graph += graph_i

        return graph, shape_to_file, class_to_shape


def load_rdf_files_into_graph(path: Path, memory_graph: Graph) -> Graph:
    extensions = [".ttl", ".n3", ".json", ".rdf"]
    for f in path.rglob(os.path.join("*.*")):
        if f.suffix in extensions:
            file_format = guess_format(f.name)
            if file_format is None:
                file_format = "json-ld"
            memory_graph.parse(f.as_posix(), format=file_format)

    return memory_graph
