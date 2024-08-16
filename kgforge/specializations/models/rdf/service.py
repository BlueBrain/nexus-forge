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
from pyshacl.validate import Validator, validate
from pyshacl.consts import SH_Violation
from pyshacl.constraints.constraint_component import CustomConstraintComponentFactory
from pyshacl.shapes_graph import ShapesGraph
from rdflib import OWL, SH, BNode, Graph, Namespace, URIRef, RDF, XSD
from rdflib.paths import ZeroOrMore
from rdflib import Dataset as RDFDataset
from rdflib.collection import Collection as RDFCollection
from rdflib.exceptions import ParserError

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


class ShapeWrapper(Shape):
    __slots__ = ("__dict__",)

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape.sg, shape.node, shape._p, shape._path, shape.logger)

    def traverse(self, predecessors: Set[URIRef]) -> Tuple[List, Dict]:
        """traverses the Shape SHACL properties to collect constrained properties

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

    def lookup_shape_from_node(self, node: URIRef) -> Optional[ShapeWrapper]:
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

        return ShapeWrapper(shape)

    @property
    def shapes(self):  # pyshacl implementation returns dict_values (not list). This cannot be pickled.
        """

        :returns: [Shape]
        :rtype: list(pyshacl.shape.Shape)
        """
        if len(self._node_shape_cache) < 1:
            self._build_node_shape_cache()
        return list(self._node_shape_cache.values())


class RdfService:

    def __init__(self, graph: RDFDataset, context_iri: Optional[str] = None) -> None:

        if context_iri is None:
            raise ConfigurationError("RdfModel requires a context")
        self._dataset_graph = graph
        self._sg = None
        self._init_shape_graph_wrapper()
        self.NXV = Namespace("https://bluebrain.github.io/nexus/vocabulary/")
        self._context_cache = {}
        resolved_context = self.resolve_context(context_iri)
        self.context = Context(resolved_context, context_iri)
        (
            self.class_to_shape,
            self.shape_to_defining_resource,
            self.defining_resource_to_named_graph,
        ) = self._build_shapes_map()
        self.ont_to_named_graph = self._build_ontology_map()
        self._imported = []
        self._defining_resource_to_imported_ontology = {}

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

    @staticmethod
    def type_to_validate_against(resource: Resource, type_: str) -> str:
        try:
            if not resource.get_type() and not type_:
                raise ValueError(
                    "No type was provided through Resource.type or the type_ parameter"
                )
            if isinstance(resource.get_type(), list) and type_ is None:
                raise ValueError(
                    "Resource has list of types as attribute and type_ parameter is not specified. "
                    "Provide a single value for the type_ parameter or for Resource.type"
                )
            type_to_validate = type_ if type_ else resource.get_type()
        except ValueError as exc:
            raise TypeError(
                f"A single type should be provided for validation: {str(exc)}"
            ) from exc

        return type_to_validate

    @staticmethod
    def validate(
            resource: Resource, shape: ShapeWrapper, shacl_graph: Graph, ont_graph: Graph, type_to_validate: str, inference: str, context: Context
    ) -> Tuple[bool, Graph, str]:

        data_graph = as_graph(resource, False, context, None, None)

        inplace = inference and inference != "none"
        conforms, report_graph, report_text = validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            ont_graph=ont_graph,
            inference=inference,
            inplace=inplace,
        )

        # when no schema target was found in the data (i.e no data was selected for validation)
        # conforms is currently set to True by pyShacl. Here it is set to False so that
        # the validation fails when type_to_validate is not present in the data
        if conforms and len(shape.focus_nodes(data_graph)) == 0:
            conforms = False
            # Create a dedicated validation report
            result_desc = (
                f"No data matching the targets (i.e. what the schema can validate) of {type_to_validate}'s schema"
                + f" were found in the provided resource. The {type_to_validate} schema can validate the following types: {list(shape.target_classes())}."
                + f" Consider providing a resource with type in {list(shape.target_classes())}."
            )
            r_node = BNode()
            result = (
                result_desc,
                r_node,
                [
                    (r_node, RDF.type, SH.ValidationResult),
                    (r_node, SH.sourceShape, (shape.sg, shape.node)),
                    (
                        r_node,
                        SH.resultSeverity,
                        SH.Warning,
                    ),  # what is the severity here ?
                ],
            )
            report_graph, report_text = Validator.create_validation_report(
                sg=shape.sg, conforms=conforms, results=[result]
            )
        return conforms, report_graph, report_text

    @abstractmethod
    def resolve_context(self, iri: str) -> Dict:
        """For a given IRI return its resolved context recursively"""
        raise NotImplementedError()

    @abstractmethod
    def generate_context(self) -> Dict:
        """Generates a JSON-LD context with the classes and terms present in the SHACL graph."""
        raise NotImplementedError()

    @abstractmethod
    def _build_shapes_map(self) -> Tuple[Dict, Dict, Dict]:
        """Index the loaded node shapes
        Returns:
            * a Dict of a targeted owl:Class to a shape
            * a Dict of a shape to the resource defining it through <https://bluebrain.github.io/nexus/vocabulary/shapes>
            * a Dict of a resource defining a shape to the a named graph containing it
        """
        raise NotImplementedError()

    @abstractmethod
    def _build_ontology_map(self) -> Dict:
        """Index the loaded ontologies
        Returns:
            * a Dict of URIRef to ontology named graph
        """
        raise NotImplementedError()

    @abstractmethod
    def load_resource_graph_from_source(self, graph_id: str, schema_id: str) -> Graph:
        """Loads into graph_id the node shapes defined in shema_id from the source

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
        self._sg = ShapesGraphWrapper(self._dataset_graph)

    def get_shape_graph_wrapper(self):
        return self._sg

    def _get_named_graph_from_shape(self, shape_uriref: URIRef):
        return self.defining_resource_to_named_graph[
            self.shape_to_defining_resource[shape_uriref]
        ]

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
                        v_prefix, v_namespace, v_name = (
                            self._dataset_graph.compute_qname(property_.path)
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
                                        px, ns, n = self._dataset_graph.compute_qname(
                                            obj_type
                                        )
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
            t_prefix, t_namespace, t_name = self._dataset_graph.compute_qname(type_)
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

    def _process_imported_resource(
        self,
        imported_resource_uriref,
        resource_to_named_graph_uriref,
        collect_imported_ontology: bool,
    ) -> Tuple[Graph, Graph]:
        imported_graph_id = resource_to_named_graph_uriref[imported_resource_uriref]
        if imported_resource_uriref not in self._imported:
            imported_resource_graph, imported_ont_graph = (
                self._transitive_load_resource_graph(
                    imported_graph_id, imported_resource_uriref
                )
            )
        else:
            imported_resource_graph = self._dataset_graph.graph(imported_graph_id)
            imported_ont_graph = Graph()
            if collect_imported_ontology:
                imported_ont_graph = self._build_imported_ontology_graph(
                    imported_resource_uriref
                )
        return imported_resource_graph, imported_ont_graph

    def _transitive_load_resource_graph(
        self, graph_uriref: URIRef, resource_uriref: URIRef
    ) -> Tuple[Graph, Graph]:
        """Loads into the graph identified by graph_uriref:
            * the node shapes defined in the resource identified by resource_uriref
            * the transitive closure of the owl.imports property (only schema) of the resource resource_uriref
           Loads imported (by resource_uriref) ontologies in a separate rdf graph ont_graph.
           Loaded schemas and ontologies are cached in self._imported.
        Args:
            graph_uriref: A named graph URIRef containing schema_uriref
            resource_uriref: the URI of a node shape
        Returns:
            A Tuple of 2 rdflib.Graph():
            * schema graph
            * imported ontology graph
        """
        resource_graph = self.load_resource_graph_from_source(
            graph_uriref, resource_uriref
        )
        ont_graph = Graph()
        transitive_imported_ontologies = []
        locally_imported_ontologies = []
        for imported in resource_graph.objects(resource_uriref, OWL.imports):
            imported_resource_uriref = URIRef(self.context.expand(imported))
            imported_resource_graph = Graph()
            if imported_resource_uriref in self.defining_resource_to_named_graph:
                imported_resource_graph, imported_ont_graph = (
                    self._process_imported_resource(
                        imported_resource_uriref,
                        self.defining_resource_to_named_graph,
                        collect_imported_ontology=True,
                    )
                )
                transitive_imported_ontologies += (
                    self._defining_resource_to_imported_ontology.get(
                        imported_resource_uriref, []
                    )
                )
            elif imported_resource_uriref in self.ont_to_named_graph:
                imported_ont_graph, _ = self._process_imported_resource(
                    imported_resource_uriref,
                    self.ont_to_named_graph,
                    collect_imported_ontology=False,
                )
                locally_imported_ontologies.append(imported_resource_uriref)
            else:
                raise ValueError(
                    f"Imported resource {imported_resource_uriref} is not loaded as schema or ontology"
                )
            try:
                # set operation to keep blank nodes unchanged as all the graphs belong to the same overall RDF Dataset
                # seeAlso: https://rdflib.readthedocs.io/en/stable/merging.html
                ont_graph += imported_ont_graph
                resource_graph += imported_resource_graph
            except ParserError as pe:
                raise ValueError(
                    f"Failed to parse the rdf graph of the imported resource {imported_resource_uriref}: {str(pe)}"
                ) from pe

        self._imported.append(resource_uriref)
        if transitive_imported_ontologies or locally_imported_ontologies:
            if resource_uriref not in self._defining_resource_to_imported_ontology:
                self._defining_resource_to_imported_ontology[resource_uriref] = []
            self._defining_resource_to_imported_ontology[resource_uriref].extend(
                transitive_imported_ontologies + locally_imported_ontologies
            )
        return resource_graph, ont_graph

    def _get_transitive_property_shapes_from_nodeshape(
        self, node_shape_uriref: URIRef, schema_graph: Graph
    ) -> Tuple[List, List, List, List]:
        """
        Recursively collect all the property shapes defined (through sh:property) by node_shape_uriref and by the node shapes
        it extends through (and|or|xone)*/SH.node. In order to properly replace in schema_graph
        the (node_shape_uriref, SH.node, parent_node_shape_uriref) triples with (node_shape_uriref, SH.property, property_shape_uriref)
        for each collected property shape, are also collected:

        * (node_shape_uriref, SH.property, property_shape_uriref) triples to add to schema_graph
        * (node_shape_uriref, SH.node, parent_node_shape_uriref) triples  to remove from schema_graph
        * RDF collection c such as (node_shape_uriref, c/SH.node, parent_node_shape_uriref) and index of items to remove from them

        Args:
            node_shape_uriref: the URI of a node shape
            schema_graph: An rdflib.Graph containing the definition of node_shape_uriref
        Returns:
            A Tuple of 3 lists:
            * the triples to add to schema_graph
            * collected property shapes (SH.property, property_shape_uriref)
            * the triples to remove from schema_graph
            * RDF Collections and index of items to remove from them
        """
        node_transitive_property_shapes = []
        triples_to_add = []
        triples_to_remove = []
        rdfcollection_items_to_remove = []
        sh_nodes, sh_properties = self.get_nodeshape_parent_propertyshape(
            self._dataset_graph, node_shape_uriref
        )
        for sh_node in set(sh_nodes):
            if str(sh_node) != str(node_shape_uriref) and str(sh_node) != str(RDF.nil):
                t_a, p_a, t_r, c_r = (
                    self._get_transitive_property_shapes_from_nodeshape(
                        sh_node, schema_graph
                    )
                )
                if p_a:
                    triples_to_add.extend(t_a)
                    rdfcollection_items_to_remove.extend(c_r)
                    for propertyShape in p_a:
                        triples_to_add.append(
                            (node_shape_uriref, propertyShape[0], propertyShape[1])
                        )
                        node_transitive_property_shapes.append(propertyShape)
                    triples_to_remove.extend(t_r)
                    triples_to_remove.append((node_shape_uriref, SH.node, sh_node))
                    for t in schema_graph.subjects(SH.node, sh_node):
                        for list_, first, o, g in self._dataset_graph.quads(
                            (
                                None,
                                URIRef(
                                    "http://www.w3.org/1999/02/22-rdf-syntax-ns#first"
                                ),
                                t,
                                None,
                            )
                        ):
                            if g == self._get_named_graph_from_shape(node_shape_uriref):
                                list_collection = RDFCollection(schema_graph, list_)
                                t_index = list_collection.index(t)
                                # del list_collection[t_index]
                                rdfcollection_items_to_remove.append(
                                    (list_collection, t_index)
                                )
        for sh_node_property in set(sh_properties):
            if str(sh_node_property) != str(node_shape_uriref) and str(
                sh_node_property
            ) != str(RDF.nil):
                node_transitive_property_shapes.append((SH.property, sh_node_property))
        return (
            triples_to_add,
            node_transitive_property_shapes,
            triples_to_remove,
            rdfcollection_items_to_remove,
        )

    def get_nodeshape_parent_propertyshape(self, graph, node_shape_uriref):
        schema_defines_shape = [
            SH["and"] / (RDF.first | RDF.rest / RDF.first) * ZeroOrMore,
            SH["or"] / (RDF.first | RDF.rest / RDF.first) * ZeroOrMore,
            SH["xone"] / (RDF.first | RDF.rest / RDF.first) * ZeroOrMore,
        ]
        sh_properties = list(graph.objects(node_shape_uriref, SH.property))
        sh_nodes = list(graph.objects(node_shape_uriref, SH.node))
        for s in schema_defines_shape:
            sh_nodes.extend(list(graph.objects(node_shape_uriref, s / SH.node)))
            sh_properties.extend(
                list(graph.objects(node_shape_uriref, s / SH.property))
            )
        return sh_nodes, sh_properties

    def _import_shape(self, node_shape_uriref: URIRef):
        try:
            shape_graph, ont_graph = self._transitive_load_resource_graph(
                self._get_named_graph_from_shape(node_shape_uriref),
                self.shape_to_defining_resource[node_shape_uriref],
            )
            # Address (though not for all node shape inheritance cases) limitation of the length
            # of sh:node transitive path (https://github.com/RDFLib/pySHACL/blob/master/pyshacl/shape.py#L468).
            (triples_to_add, _, triples_to_remove, rdfcollection_items_to_remove) = (
                self._get_transitive_property_shapes_from_nodeshape(
                    node_shape_uriref, shape_graph
                )
            )
            for triple_to_add in triples_to_add:
                shape_graph.add(triple_to_add)
            for triple_to_remove in triples_to_remove:
                shape_graph.remove(triple_to_remove)
            for (
                rdfcollection,
                rdfcollection_item_index,
            ) in rdfcollection_items_to_remove:
                del rdfcollection[rdfcollection_item_index]
            # reloads the shapes graph
            self._init_shape_graph_wrapper()
            shape = self.get_shape_graph_wrapper().lookup_shape_from_node(
                node_shape_uriref
            )
            return shape, shape_graph, ont_graph
        except Exception as e:
            raise Exception(
                f"Failed to import the shape '{node_shape_uriref}': {str(e)}"
            ) from e

    def get_shape_graph(self, node_shape_uriref: URIRef) -> Tuple[ShapeWrapper, Graph, Graph]:
        if node_shape_uriref not in self.shape_to_defining_resource:
            raise ValueError(f"Unknown shape '{node_shape_uriref}'")

        if self.shape_to_defining_resource[node_shape_uriref] not in self._imported:
            return self._import_shape(node_shape_uriref)

        try:
            shape = self.get_shape_graph_wrapper().lookup_shape_from_node(
                node_shape_uriref
            )
            shape_graph = self._dataset_graph.graph(
                self._get_named_graph_from_shape(node_shape_uriref)
            )
            ont_graph = self._build_imported_ontology_graph(
                self.shape_to_defining_resource[node_shape_uriref]
            )

            return shape, shape_graph, ont_graph

        except ValueError:
            return self._import_shape(node_shape_uriref)

    def _build_imported_ontology_graph(self, resurce_uriref):
        ont_graph = Graph()
        if (
            resurce_uriref in self._defining_resource_to_imported_ontology
        ):  # has imported ontology
            imported_ont_urirefs = self._defining_resource_to_imported_ontology[
                resurce_uriref
            ]
            for imported_ont_uriref in imported_ont_urirefs:
                if imported_ont_uriref in self.ont_to_named_graph:
                    ont_named_graph = self.ont_to_named_graph[imported_ont_uriref]
                    ont_graph += self._dataset_graph.graph(ont_named_graph)
                else:
                    raise ValueError(
                        f"Unknown ontology '{imported_ont_uriref}' imported in schema '{resurce_uriref}'"
                    )
        return ont_graph

    def get_shape_uriref_from_class_fragment(self, fragment):
        try:
            type_expanded_cls = self.context.expand(fragment)
            return self.class_to_shape[URIRef(type_expanded_cls)]
        except Exception as ke:
            raise TypeError(f"Unknown type '{fragment}': {ke}") from ke
