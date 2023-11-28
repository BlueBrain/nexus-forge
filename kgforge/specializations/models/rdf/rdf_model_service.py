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
import json
from abc import abstractmethod, ABC
from typing import List, Dict, Tuple, Set, Optional

from rdflib import Graph, URIRef, RDF, XSD
from kgforge.core.commons.sparql_query_builder import SPARQLQueryBuilder
from kgforge.core.resource import Resource
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import ConfigurationError
from kgforge.core.conversions.rdf import as_graph

from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.utils import as_term
from kgforge.specializations.models.rdf.pyshacl_shape_wrapper import ShapesGraphWrapper


class RdfModelService(ABC):

    def __init__(self, context_iri: Optional[str] = None):

        if context_iri is None:
            raise ConfigurationError("RdfModel requires a context")

        self._graph, self.shape_to_source, self.class_to_shape = self._build_shapes_map()
        self._shapes_graph = ShapesGraphWrapper(self._graph)

        self._context_cache = dict()

        self.context = Context(self.resolve_context(context_iri), context_iri)
        self.types_to_shapes: Dict[str, URIRef] = self._build_types_to_shapes()

    def get_shape_source(self, schema_iri: URIRef) -> str:
        return self.shape_to_source[schema_iri]

    def sparql(self, query: str) -> List[Resource]:
        e = self._graph.query(query)
        results = json.loads(e.serialize(format="json"))
        return SPARQLQueryBuilder.build_resource_from_select_query(results["results"]["bindings"])

    @abstractmethod
    def materialize(self, iri: URIRef) -> NodeProperties:
        """Triggers the collection of properties of a given Shape node

        Args:
            iri: the URI of the node to start collection

        Returns:
            A NodeProperty object with the collected properties
        """
        ...

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
        ...

    @abstractmethod
    def resolve_context(self, iri: str) -> Dict:
        """For a given IRI return its resolved context recursively"""
        ...

    @abstractmethod
    def generate_context(self) -> Dict:
        """Generates a JSON-LD context with the classes and terms present in the SHACL graph."""
        ...

    @abstractmethod
    def _build_shapes_map(self) -> Tuple[Graph, Dict[URIRef, str], Dict[str, URIRef]]:
        ...

    def _build_types_to_shapes(self) -> Dict[str, URIRef]:
        """Iterates the classes_to_shapes dictionary to create a term to shape dictionary filtering
         the terms available in the context """
        types_to_shapes: Dict = {}
        for k, v in self.class_to_shape.items():
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
