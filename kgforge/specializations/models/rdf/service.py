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
from typing import List, Dict, Tuple, Set, Optional
from abc import abstractmethod
from pyshacl.constraints import ALL_CONSTRAINT_PARAMETERS
from pyshacl.shape import Shape
from pyshacl.shapes_graph import ShapesGraph
from rdflib import OWL, SH, Graph, Namespace, URIRef, RDF, XSD
from rdflib.paths import ZeroOrMore
from rdflib import Dataset as RDFDataset

from kgforge.core.resource import Resource
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.core.conversions.rdf import as_graph
from kgforge.specializations.models.rdf.collectors import (
    AndCollector,
    NodeCollector,
    PropertyCollector,
    MinCountCollector,
    DatatypeCollector,
    InCollector,
    ClassCollector,
    NodeKindCollector,
    OrCollector,
    XoneCollector,
    HasValueCollector,
)
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
    HasValueCollector,
]
ALL_COLLECTORS_MAP = {c.constraint(): c for c in ALL_COLLECTORS}


def traverse(self, predecessors: Set[URIRef]) -> Tuple[List, Dict]:
    """traverses the Shape SACL properties to collect constrained properties

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
    properties = []
    attributes = {}
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
    __slots__ = ("__dict__",)

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape.sg, shape.node, shape._p, shape._path, shape.logger)

    def parameters(self):
        return (
            p
            for p, v in self.sg.predicate_objects(self.node)
            if p in ALL_CONSTRAINT_PARAMETERS
        )


class ShapesGraphWrapper(ShapesGraph):

    def __init__(self, graph: RDFDataset) -> None:
        super().__init__(graph)
        # the following line triggers the shape loading
        self._shapes = self.shapes

    def lookup_shape_from_node(self, node: URIRef) -> Shape:
        """Overwrite function to inject the transverse function for only to requested nodes.

        Args:
            node (URIRef): The node to look up.

        Returns:
            Shape: The Shacl shape of the requested node.
        """
        try:
            shape = self._node_shape_cache[node]
        except KeyError as ke:
            raise ValueError(f"Unknown shape node id '{node}': {str(ke)}") from ke
        if shape:
            shape_wrapper = ShapeWrapper(self._node_shape_cache[node])
            if not hasattr(shape_wrapper, "traverse"):
                shape_wrapper.traverse = types.MethodType(traverse, shape_wrapper)
            return shape_wrapper
        return shape


class RdfService:

    def __init__(self, graph: RDFDataset, context_iri: Optional[str] = None) -> None:

        if context_iri is None:
            raise ConfigurationError("RdfModel requires a context")
        self._graph = graph
        self._sg = None
        self._init_shape_graph_wrapper()
        self.NXV = Namespace("https://bluebrain.github.io/nexus/vocabulary/")
        self._context_cache = {}
        resolved_context = self.resolve_context(context_iri)
        self.context = Context(resolved_context, context_iri)
        (
            self.class_to_shape,
            self.shape_to_defining_resource,
            self.shape_to_named_graph,
            self.defining_resource_to_named_graph,
        ) = self._build_shapes_map()
        self._imported = []

    @abstractmethod
    def schema_source_id(self, shape_uri: str) -> str:
        """Id of the source from which the shape is accessible (e.g. bucket, file path, ...)

        Args:
            shape_uri: the URI of a node shape

        Returns:
            The id of the source from which the shape is accessible
        """
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

    def validate(self, resource: Resource, type_: str):
        try:
            if isinstance(resource.type, list) and type_ is None:
                raise ValueError(
                    "Resource has list of types as attribute and type_ parameter is not specified. "
                    "Please provide a type_ parameter to validate against it."
                )
            type_to_validate = type_ if type_ else resource.type
        except AttributeError as exc:
            raise TypeError(
                "Resource requires a type attribute or a type_ parameter should be provided"
            ) from exc
        shape_iri = self.get_shape_iri_from_class_fragment(type_to_validate)
        data_graph = as_graph(resource, False, self.context, None, None)
        shape, shacl_graph = self.get_shape_graph(shape_iri)
        return self._validate(shape_iri, data_graph, shape, shacl_graph)

    @abstractmethod
    def _validate(
        self, iri: str, data_graph: Graph, shape: Shape, shacl_graph: Graph
    ) -> Tuple[bool, Graph, str]:
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
    def _build_shapes_map(self) -> Tuple[Dict, Dict, Dict, Dict]:
        """Index the loaded node shapes
        Returns:
            * a Dict of a targeted owl:Class to a shape
            * a Dict of a shape to the resource defining it through <https://bluebrain.github.io/nexus/vocabulary/shapes>
            * a Dict of a shape to the a named graph containing it
            * a Dict of a resource defining a shape to the a named graph containing it
        """
        raise NotImplementedError()

    @abstractmethod
    def load_shape_graph(self, graph_id: str, schema_id: str) -> Graph:
        """Loads the content of the node shapes defined in by shema_id and accessible from graph_id

        Args:
            graph_id: A named graph uri from which the shapes are accessible
            schema_id: the resource defining the node shapes through <https://bluebrain.github.io/nexus/vocabulary/shapes>

        Returns:
            An rdflib.Graph() with node shapes defined by schema_id
        """
        raise NotImplementedError()

    def schema_id(self, shape_uri: str) -> str:
        """Id of the schema resource defining the node shape

        Args:
            shape_uri: the URI of a node shape

        Returns:
            The Id of the schema resource defining the node shape
        """
        return str(self.shape_to_defining_resource[URIRef(shape_uri)])

    def _init_shape_graph_wrapper(self):
        self._sg = ShapesGraphWrapper(self._graph)

    def get_shape_graph_wrapper(self):
        return self._sg

    def _generate_context(self) -> Dict:
        """Materializes all Types into templates and parses the templates to generate a context"""
        # FIXME: the status of this function is experimental
        # TODO: check if there are conflicting terms, and throw error
        context = {}
        prefixes = {}
        types_ = {}
        terms = {}

        def traverse_properties(properties) -> Tuple[Dict, Dict]:
            l_prefixes = {}
            l_terms = {}
            for property_ in properties:
                if hasattr(property_, "path"):
                    if property_.path != RDF.type and str(property_.path) != "id":
                        v_prefix, v_namespace, v_name = self._graph.compute_qname(
                            property_.path
                        )
                        l_prefixes.update({v_prefix: str(v_namespace)})
                        term_obj = {"@id": ":".join((v_prefix, v_name))}
                        if hasattr(property_, "id"):
                            term_obj.update({"@type": "@id"})
                        if hasattr(property_, "values"):
                            if (
                                isinstance(property_.values, str)
                                or len(property_.values) == 1
                            ):
                                if isinstance(property_.values, list):
                                    obj_type = property_.values[0]
                                else:
                                    obj_type = property_.values
                                if obj_type in target_classes:
                                    term_obj.update({"@type": "@id"})
                                else:
                                    try:
                                        px, ns, n = self._graph.compute_qname(obj_type)
                                        l_prefixes.update({px: str(ns)})
                                        if str(ns) == str(XSD):
                                            term_obj.update(
                                                {"@type": ":".join((px, n))}
                                            )
                                    except Exception:
                                        pass
                        l_terms.update({v_name: term_obj})
                if hasattr(property_, "properties"):
                    l_p, l_t = traverse_properties(property_.properties)
                    l_prefixes.update(l_p)
                    l_terms.update(l_t)
            return l_prefixes, l_terms

        target_classes = []
        for k in self.class_to_shape.keys():
            key = as_term(k)
            if key not in target_classes:
                target_classes.append(key)
            else:
                # TODO: should this raise an error?
                print("duplicated term", key, k)

        for type_, shape in self.class_to_shape.items():
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

        return {"@context": context} if len(context) > 0 else None

    def transitive_load_shape_graph(
        self, graph_id: str, schema_id: str, node_shape_uriref: URIRef = None
    ):
        schema_graph = self.load_shape_graph(graph_id, schema_id)
        self._imported.append(schema_id)
        for imported in schema_graph.objects(URIRef(schema_id), OWL.imports):
            imported_schema_id = self.context.expand(imported)
            imported_graph_id = self.defining_resource_to_named_graph[
                URIRef(imported_schema_id)
            ]
            if imported_schema_id not in self._imported:
                imported_schema_graph = self.transitive_load_shape_graph(
                    imported_graph_id, imported_schema_id
                )
            else:
                imported_schema_graph = self._graph.graph(URIRef(graph_id))
            schema_graph.parse(
                data=imported_schema_graph.serialize(format="n3"), format="n3"
            )
        if node_shape_uriref:
            triples_to_add, _, triples_to_remove = (
                self._get_property_shapes_from_nodeshape(node_shape_uriref)
            )
            for triple_to_add in triples_to_add:
                schema_graph.add(triple_to_add)
            for triple_to_remove in triples_to_remove:
                schema_graph.remove(triple_to_remove)
        return schema_graph

    def _get_property_shapes_from_nodeshape(self, node_shape_uriref):
        property_shapes_to_add = []
        triples_to_add = []
        triples_to_remove = []
        schema_defines_shape = [
            SH["and"] / (RDF.first | RDF.rest / RDF.first) * ZeroOrMore,
            SH["or"] / (RDF.first | RDF.rest / RDF.first) * ZeroOrMore,
            SH["xone"] / (RDF.first | RDF.rest / RDF.first) * ZeroOrMore,
        ]
        sh_nodes = []
        sh_properties = []
        sh_properties.extend(list(self._graph.objects(node_shape_uriref, SH.property)))
        sh_nodes.extend(list(self._graph.objects(node_shape_uriref, SH.node)))
        for s in schema_defines_shape:
            sh_nodes.extend(list(self._graph.objects(node_shape_uriref, s / SH.node)))
            sh_properties.extend(
                list(self._graph.objects(node_shape_uriref, s / SH.property))
            )
        for sh_node in set(sh_nodes):
            if str(sh_node) != str(node_shape_uriref) and str(sh_node) != str(RDF.nil):
                t_a, p_a, t_r = self._get_property_shapes_from_nodeshape(sh_node)
                if p_a:
                    triples_to_add.extend(t_a)
                    for propertyShape in p_a:
                        triples_to_add.append(
                            (node_shape_uriref, propertyShape[0], propertyShape[1])
                        )
                        property_shapes_to_add.append(propertyShape)
                    triples_to_remove.extend(t_r)
                    triples_to_remove.append((node_shape_uriref, SH.node, sh_node))

        for sh_node_property in set(sh_properties):
            if str(sh_node_property) != str(node_shape_uriref) and str(
                sh_node_property
            ) != str(RDF.nil):
                property_shapes_to_add.append((SH.property, sh_node_property))

        return triples_to_add, property_shapes_to_add, triples_to_remove

    def get_shape_graph(self, shape_uriref: URIRef) -> Tuple[Shape, Graph]:
        try:
            shape = self.get_shape_graph_wrapper().lookup_shape_from_node(shape_uriref)
            if (
                shape_uriref in self.shape_to_defining_resource
                and self.shape_to_defining_resource[shape_uriref] in self._imported
            ):
                shape_graph = self._graph.graph(self.shape_to_named_graph[shape_uriref])
            else:
                raise ValueError()
        except ValueError:
            try:
                shape_graph = self.transitive_load_shape_graph(
                    self.shape_to_named_graph[shape_uriref],
                    self.shape_to_defining_resource[shape_uriref],
                    shape_uriref,
                )
                # reloads the shapes graph
                self._init_shape_graph_wrapper()
                shape = self.get_shape_graph_wrapper().lookup_shape_from_node(
                    shape_uriref
                )
            except Exception as e:
                raise Exception(
                    f"Failed to get the shape '{shape_uriref}': {str(e)}"
                ) from e

        return shape, shape_graph

    def get_shape_iri_from_class_fragment(self, fragment):
        try:
            type_expanded_cls = self.context.expand(fragment)
            return self.class_to_shape[URIRef(type_expanded_cls)]
        except KeyError as ke:
            raise TypeError(f"Unknown type: {ke}") from ke
