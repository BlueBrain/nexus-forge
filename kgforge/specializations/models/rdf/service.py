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
import types
from typing import List, Dict, Tuple, Set
from urllib.parse import urlparse

from pyshacl.shape import Shape
from pyshacl.shapes_graph import ShapesGraph
from rdflib import Graph, URIRef, RDF

from kgforge.core.commons.context import Context
from kgforge.specializations.models.rdf.collectors import (AndCollector, NodeCollector,
                                                           PropertyCollector, MinCountCollector,
                                                           DatatypeCollector, InCollector,
                                                           ClassCollector, NodeKindCollector,
                                                           OrCollector, XoneCollector,
                                                           HasValueCollector)
from kgforge.specializations.models.rdf.node_properties import NodeProperties

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

    for param in iter(parameters):
        if param in ALL_COLLECTORS_MAP:
            constraint_collector = ALL_COLLECTORS_MAP[param]
            if constraint_collector not in done_collectors:
                c = constraint_collector(self)
                predecessors.add(self.node)
                props, attrs = c.collect(predecessors)
                if predecessors:
                    predecessors.pop()
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


class Service:
    """This class start the collection of Shapes"""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.sg = ShapesGraphWrapper(self.graph)
        self.shapes = self.sg.shapes
        self.class_to_shapes = self._build_shapes_map()
        self.types_shapes_map = {as_term(k): v for k, v in self.class_to_shapes.items()}
        self.context_cache = dict()

    def materialize(self, uri: URIRef) -> NodeProperties:
        """Triggers the collection of properties of a given Shape node

        Args:
            uri: the URI of the node to start collection

        Returns:
            A NodeProperty object with the collected properties
        """
        sh = self.sg.lookup_shape_from_node(uri)
        predecessors = set()
        props, attrs = sh.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def resolve_context(self, file: str) -> Dict:
        if file in self.context_cache:
            return self.context_cache[file]
        else:
            try:
                context = Context(file)
            except FileNotFoundError as e:
                raise ValueError(e)
            else:
                self.context_cache.update({file: context.document})
                return context.document

    def generate_context(self) -> Dict:
        """Generates a JSON dictionary with the classes and terms present in the
        SHACK graph.

        Returns:
            A JSON dictionary
        """
        # TODO: check if there are conflicting terms, and decide if an error should be thrown
        context = dict()
        target_classes = set(self.class_to_shapes.keys())
        prefixes = dict()
        types_ = dict()
        terms = dict()

        def traverse_properties(properties) -> Tuple[Dict, Dict]:
            l_prefixes = dict()
            l_terms = dict()
            for property_ in properties:
                if hasattr(property_, "path"):
                    if property_.path != RDF.type:
                        v_prefix, v_namespace, v_name = self.graph.compute_qname(property_.path)
                        l_prefixes.update({v_prefix: str(v_namespace)})
                        term_obj = {"@id": ":".join((v_prefix, v_name))}
                        if hasattr(property_, "id"):
                            term_obj.update({"@type": "@id"})
                        if hasattr(property_, "values"):
                            if isinstance(property_.values, str) or len(property_.values) == 1:
                                if isinstance(property_.values, list):
                                    obj_type = property_.values[0]
                                else:
                                    obj_type = property_.values
                                if obj_type in target_classes:
                                    term_obj.update({"@type": "@id"})
                                # else:
                                #     try:
                                #         px, ns, n = self.graph.compute_qname(obj_type)
                                #         l_prefixes.update({px: str(ns)})
                                #         if str(ns) == str(XSD):
                                #             term_obj.update({"@type": ":".join((px, n))})
                                #     except Exception:
                                #         pass
                        l_terms.update({v_name: term_obj})
                if hasattr(property_, "properties"):
                    l_p, l_t = traverse_properties(property_.properties)
                    l_prefixes.update(l_p)
                    l_terms.update(l_t)
            return l_prefixes, l_terms

        for type_, shape in self.class_to_shapes.items():
            t_prefix, t_namespace, t_name = self.graph.compute_qname(type_)
            prefixes.update({t_prefix: str(t_namespace)})
            types_.update({t_name: {"@id": ":".join((t_prefix, t_name))}})
            node = self.materialize(shape)
            if hasattr(node, "properties"):
                p, t = traverse_properties(node.properties)
                prefixes.update(p)
                terms.update(t)
        context.update({key: prefixes[key] for key in sorted(prefixes)})
        context.update({key: types_[key] for key in sorted(types_)})
        context.update({key: terms[key] for key in sorted(terms)})
        return {"@context":  context} if len(context) > 0 else None

    def _build_shapes_map(self) -> Dict:
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
        return {row["type"]: row["shape"] for row in res}


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
