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
import os
import types
from pathlib import Path
from typing import List, Dict, Tuple, Set
from urllib.parse import urlparse

from pyshacl.shape import Shape
from pyshacl.shapes_graph import ShapesGraph
from rdflib import Graph, URIRef
from rdflib.util import guess_format

from kgforge.specializations.models.shacl.collectors import (AndCollector, NodeCollector,
                                                             PropertyCollector, MinCountCollector,
                                                             DatatypeCollector, InCollector,
                                                             ClassCollector, NodeKindCollector,
                                                             OrCollector, XoneCollector,
                                                             HasValueCollector)
from kgforge.specializations.models.shacl.node_properties import NodeProperties

ALL_COLLECTORS = [
    AndCollector,
    OrCollector,
    PropertyCollector,
    NodeCollector,
    PropertyCollector,
    MinCountCollector,
    DatatypeCollector,
    InCollector,
    ClassCollector,
    NodeKindCollector,
    XoneCollector,
    HasValueCollector
]
ALL_COLLECTORS_MAP = {c.constraint(): c for c in ALL_COLLECTORS}


def traverse(self, predecessors: Set[URIRef]) -> Tuple[List, Dict]:
    """ traverses the Shape SACL properties to collect constrained properties

    This function is injected to pyshacl Shape object in order to traverse the Shacl graph.
    It will call a specific collector depending on the SHACL property present in the NodeShape

    Args:
        predecessors: list of nodes that have being traversed, used to break circular
            recursion

    Returns:
        properties, attributes: Tuple(list,dict), the collected properties and attributes
            respectively gathered from the collectors
    """
    parameters = self.parameters()
    properties = list()
    attributes = dict()
    done_collectors = set()
    predecessors.add(self.node)
    for p in iter(parameters):
        if p in ALL_COLLECTORS_MAP:
            constraint_collector = ALL_COLLECTORS_MAP[p]
            if constraint_collector not in done_collectors:
                c = constraint_collector(self)
                props, attrs = c.collect(predecessors)
                if attrs:
                    attributes.update(attrs)
                if props:
                    properties.extend(props)
                done_collectors.add(constraint_collector)
        else:
            # FIXME: there are some Shacl constrains that are not implemented
            # raise IndexError(f"{p} not implemented!")
            pass
    return properties, attributes


class ShapesGraphWrapper(ShapesGraph):

    def __init__(self, graph: Graph) -> None:
        super().__init__(graph)

    def lookup_shape_from_node(self, node: URIRef) -> Shape:
        """ Overwrite function to inject the transverse function for only to requested nodes.

        Args:
            node (URIRef): The node to look up.

        Returns:
            Shape: The Shacl shape of the requested node.
        """
        shape = self._node_shape_cache[node]
        if not hasattr(shape, "traverse"):
            shape.traverse = types.MethodType(traverse, shape)
        return shape


class ShapesMaterializer:
    """This class start the collection of Shapes"""

    def __init__(self, path: Path) -> None:
        self.graph = load_from_dir(path)
        self.sg = ShapesGraphWrapper(self.graph)
        self.shapes = self.sg.shapes
        self.types_shapes_map = self._build_types_shapes_map()
        self.namespaces: Dict[str, str] = dict(self.sg.graph.namespace_manager.namespaces())

    def materialize(self, uri: URIRef) -> NodeProperties:
        """Trigers the collection of properties of a given Shape node

        Args:
            type: the URI of the node to start collection

        Returns:
            A NodeProperty object with the collected properties
        """
        sh = self.sg.lookup_shape_from_node(uri)
        predecessors = set()
        props, attrs = sh.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def _build_types_shapes_map(self) -> Dict:
        res = self.graph.query(
            """
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
            }""")
        return {as_term(row["type"]): row["shape"] for row in res}


def load_from_dir(path: Path) -> Graph:
    memory_graph = Graph()
    extensions = [".ttl", ".n3", ".json", ".rdf"]
    for f in path.rglob(os.path.join("*.*")):
        if f.suffix in extensions:
            file_format = guess_format(f.name)
            if file_format is None:
                file_format = "json-ld"
            g = Graph()
            g.parse(f.as_posix(), format=file_format)
            memory_graph += g
    return memory_graph


def split_uri(uri):
    parsed = urlparse(uri)
    if parsed.fragment:
        fragment = parsed.fragment
    else:
        path_split = parsed.path.split("/")
        fragment = path_split[len(path_split)-1]
    return uri.replace(fragment, ""), fragment


def as_term(value: str) -> str:
    try:
        return split_uri(value)[1]
    except AttributeError:
        return value
