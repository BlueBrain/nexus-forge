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

from pyshacl import Validator
from rdflib import Graph, URIRef
from rdflib.util import guess_format

from kgforge.core.commons.context import Context
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.service import RdfService, ShapesGraphWrapper


class DirectoryService(RdfService):

    def __init__(self, dirpath: Path, context_iri: str) -> None:
        self._graph = load_rdf_files(dirpath)
        self._sg = ShapesGraphWrapper(self._graph)
        super().__init__(self._graph, context_iri)

    def schema_source_id(self, schema_iri: str) -> str:
        # FIXME should return the file path where the schema is in
        return schema_iri

    def materialize(self, iri: URIRef) -> NodeProperties:
        sh = self._sg.lookup_shape_from_node(iri)
        predecessors = set()
        props, attrs = sh.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def _validate(self, iri: str, data_graph: Graph) -> Tuple[bool, Graph, str]:
        validator = Validator(data_graph, shacl_graph=self._graph)
        return validator.run()

    def resolve_context(self, iri: str) -> Dict:
        if iri in self._context_cache:
            return self._context_cache[iri]
        else:
            try:
                context = Context(iri)
            except FileNotFoundError as e:
                raise ValueError(e)
            else:
                self._context_cache.update({iri: context.document})
                return context.document

    def generate_context(self) -> Dict:
        return self._generate_context()

    def _build_shapes_map(self) -> Dict:
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
            } ORDER BY ?type"""
        res = self._graph.query(query)
        return {row["type"]: row["shape"] for row in res}


def load_rdf_files(path: Path) -> Graph:
    memory_graph = Graph()
    extensions = [".ttl", ".n3", ".json", ".rdf"]
    for f in path.rglob(os.path.join("*.*")):
        if f.suffix in extensions:
            file_format = guess_format(f.name)
            if file_format is None:
                file_format = "json-ld"
            memory_graph.parse(f.as_posix(), format=file_format)
    return memory_graph
