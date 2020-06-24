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

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional, Set

from pyshacl.constraints.core.cardinality_constraints import SH_minCount
from pyshacl.constraints.core.logical_constraints import SH_and, SH_or, SH_xone
from pyshacl.constraints.core.other_constraints import SH_in, SH_hasValue
from pyshacl.constraints.core.value_constraints import SH_class, SH_nodeKind, SH_datatype
from pyshacl.consts import SH_property, SH_node, SH_IRI, SH_BlankNodeOrIRI, SH_targetClass
from pyshacl.shape import Shape
from rdflib import RDF
from rdflib.term import URIRef, BNode

from kgforge.specializations.models.rdf.node_properties import NodeProperties


ID_URI = URIRef('id')


class Collector(ABC):
    """Collector abstract class

    Depending on the constraint, a set of properties and attributes may be
    collected through the collect function.

    Attributes:
        shape: the Shacl Shape used by the collector
    """

    def __init__(self, shape: Shape) -> None:
        self.shape = shape

    @classmethod
    @abstractmethod
    def constraint(cls) -> URIRef:
        """Returns the Shacl constraint URI of the collector"""
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def collect(cls, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                         Optional[Dict]]:
        """ depending on the constraint, this function will return properties, attributes or
        both.

        Args:
            predecessors: list of nodes that have being traversed, used to break circular
                recursion

        Returns:
            properties, attributes: Tuple(list,dict), the collected properties and attributes
                respectively
        """
        raise NotImplementedError()

    def get_shape_target_classes(self) -> List:
        """Returns a list of target and implicit classes if any of the shape

        Returns:
            list of URIs
        """
        (_, target_classes, implicit_classes, _, _) = self.shape.target()
        target_classes = set(target_classes)
        target_classes.update(set(implicit_classes))
        return list(target_classes)


class HasValueCollector(Collector):
    """This class will collect values in the sh:hasValue constraint as attribute"""
    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.has_value = next(shape.objects(SH_hasValue))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_hasValue

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        attrs = dict()
        attrs["values"] = self.has_value
        return None, attrs


class DatatypeCollector(Collector):
    """This class will collect values in the sh:datatype constraint as attribute"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.data_type_rule = next(self.shape.objects(SH_datatype))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_datatype

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        attrs = dict()
        attrs["values"] = self.data_type_rule
        return None, attrs


class MinCountCollector(Collector):
    """This class will collect values in the sh:minCount constraint as attribute"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.min_count = next(self.shape.objects(SH_minCount))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_minCount

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        attrs = dict()
        attrs["mandatory"] = True if self.min_count.toPython() >= 1 else False
        return None, attrs


class NodeKindCollector(Collector):
    """This class will collect values in the sh:nodeKind constraint as attribute"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.node_kind_rule = next(self.shape.objects(SH_nodeKind))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_nodeKind

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        properties = list()
        if self.node_kind_rule == SH_IRI:
            properties.append(id_node_property(True))
        elif self.node_kind_rule == SH_BlankNodeOrIRI:
            properties.append(id_node_property(False))

        return properties, None


class InCollector(Collector):
    """This class will collect values in the sh:in constraint as attribute"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        sg = self.shape.sg.graph
        self.in_list = next(self.shape.objects(SH_in))
        self.in_values = set(sg.items(self.in_list))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_in

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        attrs = dict()
        attrs.update(constraint="in")
        attrs.update(values=[v.toPython() for v in self.in_values])
        return None, attrs


class ClassCollector(Collector):
    """This class will collect values in the sh:class constraint as attribute"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.class_rules = list(self.shape.objects(SH_class))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_class

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        attributes = dict()
        properties = list()
        for target_class in self.class_rules:
            target_class_shapes = [s for s in self.shape.sg.graph.subjects(SH_targetClass, target_class)]
            if target_class_shapes:
                for target_class_shape in target_class_shapes:
                    target_shape = self.shape.get_other_shape(target_class_shape)
                    if target_shape.node not in predecessors:
                        props, attrs = target_shape.traverse(predecessors)
                        if props:
                            attrs.update(properties=props)
                        properties.append(NodeProperties(**attrs))
                    else:
                        properties.append(type_node_property(target_class, True))
                        properties.append(id_node_property(True))
            else:
                properties.append(id_node_property(True))
                properties.append(type_node_property(target_class, True))

        # TODO: if we want not to navigate into the Class, use only attributes instead of
        #  the above for loop
        # attributes = {
        #     "path": RDF.type,
        #     "values":  [v for v in self.class_rules]
        # }
        return properties, attributes


class NodeCollector(Collector):
    """This class will collect values in the sh:node constraint as properties or
    attributes"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.node_shapes = list(self.shape.objects(SH_node))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_node

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        properties = list()
        attributes = dict()
        for n_shape in self.node_shapes:
            ns = self.shape.get_other_shape(n_shape)
            if ns.node not in predecessors:
                props, attrs = ns.traverse(predecessors)
                if ns.path() is not None:
                    if not isinstance(ns.path(), BNode):
                        attrs["path"] = ns.path()
                        if props:
                            attrs["properties"] = props
                        p = NodeProperties(**attrs)
                        properties.append(p)
                else:
                    properties.extend(props)
                    attributes.update(attrs)

        return properties, attributes


class PropertyCollector(Collector):
    """This class will collect values in the sh:property constraint as properties or
        attributes"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.property_shapes = list(self.shape.objects(SH_property))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_property

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        properties = list()
        for p_shape in self.property_shapes:
            ps = self.shape.get_other_shape(p_shape)
            if ps.node not in predecessors:
                props, attrs = ps.traverse(predecessors)
                if ps.path() is not None:
                    if not isinstance(ps.path(), BNode):
                        attrs["path"] = ps.path()
                        if props:
                            attrs["properties"] = props
                        p = NodeProperties(**attrs)
                        properties.append(p)

        types = self.get_shape_target_classes()
        if len(types) > 0:
            properties.append(type_node_property(types, True))

        return properties, None


class AndCollector(Collector):
    """This class will collect values in the sh:and constraint as properties"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.and_list = list(self.shape.objects(SH_and))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_and

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        properties = list()
        sg = self.shape.sg.graph
        for and_c in self.and_list:
            and_list = set(sg.items(and_c))
            for and_shape in and_list:
                and_shape = self.shape.get_other_shape(and_shape)
                if and_shape.node not in predecessors:
                    p, a = and_shape.traverse(predecessors)
                    if a is not None:
                        if and_shape.path() is not None:
                            if not isinstance(and_shape.path(), BNode):
                                a["path"] = and_shape.path()
                        if len(p) > 0:
                            a["properties"] = p
                        node = NodeProperties(**a)
                        properties.append(node)
                    else:
                        properties.extend(p)
        types = self.get_shape_target_classes()
        if len(types) > 0:
            properties.append(type_node_property(types, True))
        return properties, None


class OrCollector(Collector):
    """This class will collect values in the sh:and constraint as properties"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.or_list = list(self.shape.objects(SH_or))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_or

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        properties = list()
        attributes = dict()
        sg = self.shape.sg.graph
        for or_c in self.or_list:
            or_list = set(sg.items(or_c))
            for or_shape in or_list:
                or_shape = self.shape.get_other_shape(or_shape)
                if or_shape.node not in predecessors:
                    props, attrs = or_shape.traverse(predecessors)
                    if or_shape.path() is not None:
                        # This Node concerns PropertyNode options
                        if not isinstance(or_shape.path(), BNode):
                            attrs["path"] = or_shape.path()
                            if props:
                                attrs["properties"] = props
                            node = NodeProperties(**attrs)
                            properties.append(node)
                    else:
                        # This concerns ShapeNode options
                        if props:
                            properties.extend(props)
                            if len(properties) > 1:
                                mandatory_ids = get_nodes_path(properties, ID_URI, "mandatory")
                                types = get_nodes_path(properties, RDF.type, "values")
                                properties.clear()
                                if mandatory_ids:
                                    is_mandatory = any(x for x in mandatory_ids)
                                    properties.append(id_node_property(is_mandatory))
                                if types:
                                    properties.append(type_node_property(types, True))
                        elif attrs:
                            attributes = merge_dicts(attributes, attrs)
        types = self.get_shape_target_classes()
        if len(types) > 0:
            properties.append(type_node_property(types, True))
        attributes["constraint"] = "or"
        return properties, attributes


class XoneCollector(Collector):
    """This class will collect values in the sh:and constraint as properties"""

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape)
        self.xone_list = list(self.shape.objects(SH_xone))

    @classmethod
    def constraint(cls) -> URIRef:
        return SH_xone

    def collect(self, predecessors: Set[URIRef]) -> Tuple[Optional[List[NodeProperties]],
                                                          Optional[Dict]]:
        properties = list()
        attributes = dict()
        sg = self.shape.sg.graph

        for xone_c in self.xone_list:
            xone_list = set(sg.items(xone_c))
            for xone_shape in xone_list:
                xone_shape = self.shape.get_other_shape(xone_shape)
                if xone_shape.node not in predecessors:
                    props, attrs = xone_shape.traverse(predecessors)
                    if xone_shape.path() is not None:
                        # This Node concerns PropertyNode options
                        if not isinstance(xone_shape.path(), BNode):
                            attrs["path"] = xone_shape.path()
                            if props:
                                attrs["properties"] = props
                            node = NodeProperties(**attrs)
                            properties.append(node)
                    else:
                        # This concerns ShapeNode options
                        if props:
                            properties.extend(props)
                            if len(properties) > 1:
                                mandatory_ids = get_nodes_path(properties, ID_URI, "mandatory")
                                types = get_nodes_path(properties, RDF.type, "values")
                                properties.clear()
                                if mandatory_ids:
                                    is_mandatory = any(x for x in mandatory_ids)
                                    properties.append(id_node_property(is_mandatory))
                                if types:
                                    properties.append(type_node_property(types, False))
                        elif attrs:
                            attributes = merge_dicts(attributes, attrs)
        types = self.get_shape_target_classes()
        if len(types) > 0:
            properties.append(type_node_property(types, True))

        attributes["constraint"] = "xone"
        return properties, attributes


# TODO: create some factories for NodeProperties

def type_node_property(types, mandatory: bool) -> NodeProperties:
    attrs = {"path": RDF.type, "values": types, "mandatory": mandatory}
    return NodeProperties(**attrs)


def id_node_property(mandatory: bool) -> NodeProperties:
    attrs = {"path": ID_URI, "mandatory": mandatory}
    return NodeProperties(**attrs)


def merge_dicts(first: Dict, second: Dict):
    result = dict()
    result.update({k: first[k] for k in first.keys() - second.keys()})
    result.update({k: second[k] for k in second.keys() - first.keys()})
    same = first.keys() & second.keys()
    for k in same:
        if str(first[k]) == str(second[k]):
            result[k] = first[k]
        else:
            if isinstance(first[k], list):
                if isinstance(second[k], list):
                    result[k] = list(set(first[k]) | set(second[k]))
                else:
                    result[k] = first[k]
                    result[k].append(second[k])
            else:
                if isinstance(second[k], list):
                    result[k] = second[k]
                    result[k].append(first[k])
                else:
                    result[k] = [first[k], second[k]]
    return result


def get_nodes_path(nodes: List, path: URIRef, field: str):
    if len(nodes) == 0:
        return None, []
    elif len(nodes) == 1:
        types = get_node_path(nodes[0], path, field)
    else:
        types = get_node_path(nodes[0], path, field)
        for node in nodes[1:]:
            second_types = get_node_path(node, path, field)
            types = types + second_types
    return types


def get_node_path(node: NodeProperties, path: URIRef, field: str):
    result = list()
    if hasattr(node, "properties"):
        for pp in node.properties:
            if hasattr(pp, "path"):
                if pp.path == path:
                    values = getattr(pp, field, None)
                    if isinstance(values, list):
                        result.extend(values)
                    else:
                        result.append(values)
    return result
