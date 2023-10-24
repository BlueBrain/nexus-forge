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
from typing import List, Dict, Tuple, Set, Optional
from pyshacl.shape import Shape
from pyshacl.shapes_graph import ShapesGraph
from rdflib import Graph, URIRef, RDF, XSD
from rdflib.plugins.sparql.processor import SPARQLResult

from kgforge.core import Resource
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.core.conversions.rdf import as_graph

from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.utils import as_term


class RdfModelService:
    schema_to_source: Dict[URIRef, str]
    classes_to_shapes: Dict[str, URIRef]

    def __init__(self, graph: Graph, context_iri: Optional[str] = None) -> None:

        if context_iri is None:
            raise ConfigurationError("RdfModel requires a context")
        self._graph = graph
        self._context_cache = {}
        self.schema_to_source, self.classes_to_shapes = self._build_shapes_map()
        self.context = Context(self.resolve_context(context_iri), context_iri)
        self.types_to_shapes: Dict[str, URIRef] = self._build_types_to_shapes()

    def schema_source(self, schema_iri: URIRef) -> str:
        return self.schema_to_source[schema_iri]

    def sparql(self, query: str) -> SPARQLResult:
        return self._graph.query(query)

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

        if "type" not in resource.__dict__:
            raise TypeError("Resource requires a type attribute")

        if isinstance(resource.type, list) and type_ is None:
            raise ValueError(
                "Resource has list of types as attribute and type_ parameter is not specified. "
                "Please provide a type_ parameter to validate against it."
            )

        shape_iri = self.types_to_shapes.get(resource.type if type_ is None else type_, None)

        if shape_iri is None:
            raise ValueError(f"Unknown type {type_}")

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
    def _build_shapes_map(self) -> Tuple[Dict[URIRef, str], Dict[str, URIRef]]:
        """Queries the source and returns a map of owl:Class to sh:NodeShape"""
        raise NotImplementedError()

    def _build_types_to_shapes(self) -> Dict[str, URIRef]:
        """Iterates the classes_to_shapes dictionary to create a term to shape dictionary filtering
         the terms available in the context """
        types_to_shapes: Dict = {}
        for k, v in self.classes_to_shapes.items():
            term = self.context.find_term(str(k))
            if term:
                if term.name not in types_to_shapes:
                    types_to_shapes[term.name] = v
                else:
                    print("WARN: duplicated term", term.name, k, [term.name], v)
            else:
                print(f"WARN: missing term: {str(k)} in context")

        return types_to_shapes

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
                                        px, ns, n = self._graph.compute_qname(obj_type)
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

        target_classes = []
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

        return {"@context": context} if len(context) > 0 else None
