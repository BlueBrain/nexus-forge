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
import types
from abc import abstractmethod
from pyshacl.constraints import ALL_CONSTRAINT_PARAMETERS
from typing import List, Dict, Tuple, Set, Optional
from pyshacl.shape import Shape
from pyshacl.shapes_graph import ShapesGraph
from rdflib import Graph, URIRef, RDF, XSD

from kgforge.core import Resource
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.core.conversions.rdf import as_graph
from kgforge.specializations.models.rdf.collectors import (AndCollector, NodeCollector,
                                                           PropertyCollector, MinCountCollector,
                                                           DatatypeCollector, InCollector,
                                                           ClassCollector, NodeKindCollector,
                                                           OrCollector, XoneCollector,
                                                           HasValueCollector)
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.utils import as_term

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
                if attrs:
                    attributes.update(attrs)
                if props:
                    properties.extend(props)
                done_collectors.add(constraint_collector)
                if predecessors:
                    predecessors.remove(self.node)
        else:
            # FIXME: there are some SHACL constrains that are not implemented
            # raise IndexError(f"{param} not implemented!")
            pass

    return properties, attributes


class ShapeWrapper(Shape):
    __slots__ = ('__dict__',)

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape.sg, shape.node, shape._p, shape._path, shape.logger)

    def parameters(self):
        return (p for p, v in self.sg.predicate_objects(self.node)
                if p in ALL_CONSTRAINT_PARAMETERS)


class ShapesGraphWrapper(ShapesGraph):

    def __init__(self, graph: Graph) -> None:
        super().__init__(graph)
        # the following line triggers the shape loading
        self._shapes = self.shapes

    def lookup_shape_from_node(self, node: URIRef) -> Shape:
        """ Overwrite function to inject the transverse function for only to requested nodes.

        Args:
            node (URIRef): The node to look up.

        Returns:
            Shape: The Shacl shape of the requested node.
        """
        shape = self._node_shape_cache[node]
        if shape:
            shape_wrapper = ShapeWrapper(self._node_shape_cache[node])
            if not hasattr(shape_wrapper, "traverse"):
                shape_wrapper.traverse = types.MethodType(traverse, shape_wrapper)
            return shape_wrapper
        return shape


class RdfService:

    def __init__(self, graph: Graph, context_iri: Optional[str] = None) -> None:

        if context_iri is None:
            raise ConfigurationError(f"RdfModel requires a context")
        self._graph = graph
        self._context_cache = dict()
        self.classes_to_shapes = self._build_shapes_map()
        resolved_context = self.resolve_context(context_iri)
        self.context = Context(resolved_context, context_iri)
        self.types_to_shapes: Dict = self._build_types_to_shapes()

    def schema_source_id(self, schema_iri: str) -> str:
        # POLICY Should return the id of the resource containing the schema
        raise NotImplementedError()

    @abstractmethod
    def materialize(self, iri: URIRef) -> NodeProperties:
        """Triggers the collection of properties of a given Shape node

        Args:
            iri: the URI of the node to start collection

        Returns:
            A NodeProperty object with the collected properties
        """
        raise NotImplementedError()

    def validate(self, resource: Resource):
        try:
            shape_iri = self.types_to_shapes[resource.type]
        except AttributeError:
            raise TypeError("resource requires a type attribute")
        else:
            data_graph = as_graph(resource, False, self.context, None, None)
            return self._validate(shape_iri, data_graph)

    @abstractmethod
    def _validate(self, iri: str, data_graph: Graph) -> Tuple[bool, Graph, str]:
        raise NotImplementedError()

    @abstractmethod
    def resolve_context(self, iri: str) -> Dict:
        """For a given IRI return its resolved context recursively"""
        raise NotImplementedError()

    @abstractmethod
    def generate_context(self) -> Dict:
        """Generates a JSON-LD context with the classes and terms present in the SHACL graph."""
        raise NotImplementedError()

    @abstractmethod
    def _build_shapes_map(self) -> Dict:
        """Queries the source and returns a map of owl:Class to sh:NodeShape"""
        raise NotImplementedError()

    def _build_types_to_shapes(self):
        """Iterates the classes_to_shapes dictionary to create a term to shape dictionary filtering
         the terms available in the context """
        types_to_shapes: Dict = dict()
        for k, v in self.classes_to_shapes.items():
            term = self.context.find_term(str(k))
            if term:
                key = term.name
                if term.name not in types_to_shapes:
                    types_to_shapes[term.name] = v
                else:
                    print("WARN: duplicated term", key, k, [key], v)
        return types_to_shapes

    def _generate_context(self) -> Dict:
        """Materializes all Types into templates and parses the templates to generate a context"""
        # FIXME: the status of this function is experimental
        # TODO: check if there are conflicting terms, and throw error
        context = dict()
        prefixes = dict()
        types_ = dict()
        terms = dict()

        def traverse_properties(properties) -> Tuple[Dict, Dict]:
            l_prefixes = dict()
            l_terms = dict()
            for property_ in properties:
                if hasattr(property_, "path"):
                    if property_.path != RDF.type and str(property_.path) != "id":
                        v_prefix, v_namespace, v_name = self._graph.compute_qname(property_.path)
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
                                else:
                                    try:
                                        px, ns, n = self.graph.compute_qname(obj_type)
                                        l_prefixes.update({px: str(ns)})
                                        if str(ns) == str(XSD):
                                            term_obj.update({"@type": ":".join((px, n))})
                                    except Exception:
                                        pass
                        l_terms.update({v_name: term_obj})
                if hasattr(property_, "properties"):
                    l_p, l_t = traverse_properties(property_.properties)
                    l_prefixes.update(l_p)
                    l_terms.update(l_t)
            return l_prefixes, l_terms

        target_classes = list()
        for k in self.classes_to_shapes.keys():
            key = as_term(k)
            if key not in target_classes:
                target_classes.append(key)
            else:
                # TODO: should this raise an error?
                print("duplicated term", key, k)

        for type_, shape in self.classes_to_shapes.items():
            t_prefix, t_namespace, t_name = self._graph.compute_qname(type_)
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
